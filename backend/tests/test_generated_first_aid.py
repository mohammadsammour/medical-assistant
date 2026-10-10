import json
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

import main


class GeneratedFirstAidTests(unittest.TestCase):
    message = (
        "I am 25 and have a mild dry cough for two days. "
        "No fever, breathlessness or chest pain. No chronic conditions or medications."
    )
    steps = ["Generated step one.", "Generated step two.", "Generated step three."]

    def setUp(self):
        self.reply = main.ModelReply(
            status="assessment", message="Summary", symptom_summary=self.message,
            is_followup_question=False, needs_immediate_help=False, language="en",
        )
        self.history = [main.types.Content(
            role="user", parts=[main.types.Part(text=self.message)]
        )]
        self.profile = {
            "age": 25, "chronic_conditions": [], "medications": [],
            "allergies": [], "medical_history": [],
        }

    def decision(self, **overrides):
        result = {
            "rule_id": "cold_self_care", "reason": "Synthetic checked decision.",
            "evidence_quotes": ["mild dry cough"],
            "adult_age_confirmed": True, "mild_short_duration": True,
            "relevant_warning_signs_explicitly_denied": True,
            "relevant_risk_factors_checked": True,
            "no_conflicting_or_concerning_information": True,
            "first_aid_steps": self.steps,
        }
        result.update(overrides)
        return result

    @contextmanager
    def provider(self, decision=None, text=None, finish_reason=None):
        response = SimpleNamespace(
            candidates=[SimpleNamespace(
                finish_reason=finish_reason or main.types.FinishReason.STOP
            )],
            text=text if text is not None else json.dumps(decision or self.decision()),
        )
        with patch.object(main.genai, "Client") as client:
            generate = client.return_value.__enter__.return_value.models.generate_content
            generate.return_value = response
            yield generate

    def build(self):
        return main.build_final_assessment(self.reply, self.history, self.profile)

    def test_generated_steps_replace_templates_without_changing_urgency(self):
        with self.provider() as generate:
            assessment, urgency, sources = self.build()
        self.assertEqual(urgency, "potentially_self_care")
        self.assertEqual(assessment.rule_id, "cold_self_care")
        self.assertEqual([a.instruction for a in assessment.actions_now], self.steps)
        self.assertTrue(all(a.source_ids == [] for a in assessment.actions_now))
        self.assertTrue(sources)
        generate.assert_called_once()
        config = generate.call_args.kwargs["config"]
        self.assertIs(config.response_schema, main.FinalDecision)
        self.assertIn("first_aid_steps", config.system_instruction)
        self.assertIn("Do not prescribe medication", config.system_instruction)

    def test_steps_follow_requested_language(self):
        self.reply.language = "ar"
        steps = ["خطوة مولدة أولى", "خطوة مولدة ثانية", "خطوة مولدة ثالثة"]
        with self.provider(self.decision(first_aid_steps=steps)) as generate:
            assessment, _, _ = self.build()
        self.assertEqual([a.instruction for a in assessment.actions_now], steps)
        self.assertIn("Write reason and first_aid_steps in Arabic", generate.call_args.kwargs["config"].system_instruction)

    def test_steps_are_trimmed_and_deduplicated(self):
        steps = [" Generated step one. ", "", "Generated step one.", *self.steps[1:]]
        with self.provider(self.decision(first_aid_steps=steps)):
            assessment, _, _ = self.build()
        self.assertEqual([a.instruction for a in assessment.actions_now], self.steps)

    def test_missing_or_incomplete_steps_use_existing_fallback(self):
        for steps in (None, [], [" "], ["Only one step"], [str(i) for i in range(7)]):
            with self.subTest(steps=steps):
                decision = self.decision(first_aid_steps=steps)
                if steps is None:
                    del decision["first_aid_steps"]
                with self.provider(decision):
                    assessment, urgency, _ = self.build()
                self.assertEqual(urgency, "potentially_self_care")
                self.assertEqual(assessment.actions_now[1].instruction, main.GUIDANCE["cold"]["actions"][0][0])
                self.assertTrue(all(a.source_ids for a in assessment.actions_now))

    def test_non_self_care_classifications_are_preserved(self):
        for rule, urgency in (("cold_routine", "routine_consultation"), ("headache_urgent", "urgent_medical_attention")):
            with self.subTest(rule=rule), self.provider(self.decision(rule_id=rule)):
                assessment, actual, _ = self.build()
            self.assertEqual(actual, urgency)
            self.assertEqual([a.instruction for a in assessment.actions_now], self.steps)
            self.assertEqual(assessment.recommended_action, {
                "routine_consultation": "Arrange an appointment with a healthcare professional.",
                "urgent_medical_attention": "Seek an urgent medical assessment today.",
            }[urgency])

    def test_rejected_decisions_cannot_supply_steps(self):
        cases = [
            self.decision(evidence_quotes=["invented symptom"]),
            self.decision(adult_age_confirmed=None),
        ]
        for decision in cases:
            with self.subTest(decision=decision), self.provider(decision), patch.object(main, "generate_open_guidance", return_value=None):
                assessment, urgency, _ = self.build()
            self.assertEqual(urgency, "unable_to_determine")
            self.assertNotIn(self.steps[0], [a.instruction for a in assessment.actions_now])

    def test_profile_guard_still_rejects_self_care(self):
        self.profile["chronic_conditions"] = ["synthetic condition"]
        with self.provider(), patch.object(main, "generate_open_guidance", return_value=None):
            assessment, urgency, _ = self.build()
        self.assertEqual(urgency, "unable_to_determine")
        self.assertNotIn(self.steps[0], [a.instruction for a in assessment.actions_now])

    def test_early_emergency_does_not_call_provider(self):
        self.reply.needs_immediate_help = True
        with patch.object(main.genai, "Client") as client:
            assessment, urgency, _ = self.build()
        client.assert_not_called()
        self.assertEqual(urgency, "emergency")
        self.assertEqual(assessment.rule_id, "model_emergency_alert")
        self.assertIn("emergency", assessment.actions_now[0].instruction)

    def test_classified_emergency_keeps_immediate_predefined_actions(self):
        with self.provider(self.decision(rule_id="headache_emergency")):
            assessment, urgency, _ = self.build()
        self.assertEqual(urgency, "emergency")
        self.assertNotIn(self.steps[0], [a.instruction for a in assessment.actions_now])
        self.assertTrue(all(a.source_ids for a in assessment.actions_now))

    def test_failed_or_invalid_provider_reply_keeps_fallback(self):
        for text, finish in (("invalid json", None), ("{}", main.types.FinishReason.MAX_TOKENS)):
            with self.subTest(text=text), self.provider(text=text, finish_reason=finish), patch.object(main, "generate_open_guidance", return_value=None):
                _, urgency, _ = self.build()
            self.assertEqual(urgency, "unable_to_determine")
        with self.provider() as generate, patch.object(main, "generate_open_guidance", return_value=None):
            generate.side_effect = httpx.ConnectError("Synthetic connection failure")
            _, urgency, _ = self.build()
        self.assertEqual(urgency, "unable_to_determine")

    def test_api_returns_generated_steps_in_existing_response_fields(self):
        session_id = "generated-steps-regression"
        response = SimpleNamespace(candidates=[SimpleNamespace(content=main.types.Content(
            role="model", parts=[main.types.Part(text="Synthetic summary")]
        ))])
        try:
            with self.provider(), patch.object(main, "ask_gemini", return_value=(response, self.reply)), patch.object(main, "search_medical_information", return_value=([], [], None)):
                result = TestClient(main.app).post("/ai/chat", json={
                    "session_id": session_id, "message": self.message,
                    "medical_profile": self.profile,
                })
            self.assertEqual(result.status_code, 200)
            data = result.json()
            self.assertEqual(data["urgency"], "potentially_self_care")
            self.assertEqual([a["instruction"] for a in data["assessment"]["actions_now"]], self.steps)
            self.assertTrue(all(set(a) == {"instruction", "source_ids"} for a in data["assessment"]["actions_now"]))
            self.assertNotIn("first_aid_steps", data["assessment"])
        finally:
            main.sessions.pop(session_id, None)


if __name__ == "__main__":
    unittest.main()
