# MedicZero — AI Service Contract

> Historical contract for the original mock frontend and a proposed external
> service. The current integration uses the stateful FastAPI `/ai/chat` endpoint,
> not `/v1/assess/step` or `/v1/profile/extract`. `remoteAi.js` translates that
> response into the frontend shapes described below, but the old confidence,
> extra-question, treatment, and safety guarantees do not describe the running
> app. See the [current API reference](../README.md#api-reference) and
> [backend documentation](../backend/README.md).

This is the agreement between the **website** (React, frontend only, data in localStorage) and the **AI service** (built separately). The website already works against a mock that follows this exact contract. When the AI service implements it, the website switches with `VITE_AI_MODE=remote` and nothing else changes.

> The website calls the AI service **directly from the browser**, so the AI service must **enable CORS** for the website origin (e.g. `http://localhost:5173` and the deployed URL).

**If you need to change this format, agree on it with the frontend first.**

---

## 1. General

| Item | Value |
|---|---|
| Base URL | configured in the website as `VITE_AI_SERVICE_URL` (e.g. `http://localhost:8000`) |
| CORS | **required** — allow the website origin, methods `GET, POST`, header `Content-Type` |
| Auth | none (MVP) |
| Format | JSON (UTF-8), except `/v1/profile/extract` which is multipart |
| Language | all user-facing text in **Arabic (Jordanian, simple)** unless `lang: "en"` |
| Timeout | the website waits **25 s**, retries once on timeout / 5xx |
| Statelessness | the service keeps **no state**. Every call contains the full history. No database. |
| Health | `GET /health` → `{ "status": "ok", "version": "x.y.z" }` |

Errors: HTTP 4xx/5xx with `{ "error": { "code": "STRING", "message": "..." } }`.
Codes: `BAD_REQUEST`, `UNSUPPORTED_FILE`, `LLM_TIMEOUT`, `LLM_INVALID_OUTPUT`, `INTERNAL`.

---

## 2. `POST /v1/profile/extract`

Reads a medical report / prescription (PDF or image) and returns profile fields to **prefill** the sign-up form. The user reviews everything before saving.

**Request:** multipart, field `file` (`application/pdf`, `image/jpeg`, `image/png`, `image/webp`, ≤10 MB).

**Response 200:**
```json
{
  "age": 45,
  "gender": "MALE",
  "conditions": ["DIABETES", "HYPERTENSION"],
  "diabetesType": "TYPE2",
  "otherConditions": [],
  "allergies": ["Penicillin"],
  "medications": [
    { "name": "Warfarin",  "dose": "5 mg",   "frequency": "once daily",  "isAnticoagulant": true },
    { "name": "Metformin", "dose": "500 mg", "frequency": "twice daily", "isAnticoagulant": false }
  ],
  "fieldConfidence": { "age": "high", "conditions": "high", "medications": "medium" },
  "warnings": ["الجرعات غير واضحة بالصورة"]
}
```
Any field may be `null` / empty if not found. Never guess values that are not in the document.

Allowed `conditions` codes: `DIABETES, HYPERTENSION, HEART_DISEASE, ASTHMA, KIDNEY_DISEASE, LIVER_DISEASE, EPILEPSY, BLEEDING_DISORDER, THYROID, IMMUNODEFICIENCY`.
`isAnticoagulant: true` for anticoagulants **and** antiplatelets (warfarin, rivaroxaban, apixaban, dabigatran, heparin/enoxaparin, clopidogrel, aspirin used as a blood thinner…).

---

## 3. `POST /v1/assess/step`

Called on **every step** of an assessment: once at the start, then after every answer. The website sends the full history each time.

### 3.1 Request
```json
{
  "lang": "ar",
  "input": {
    "text": "انسكبت عليّ مي مغلية على ظهر إيدي اليمين قبل 5 دقايق",
    "images": [{ "mime": "image/jpeg", "base64": "/9j/4AAQ..." }]
  },
  "profile": {
    "age": 45, "gender": "MALE", "pregnant": null,
    "conditions": ["DIABETES", "HYPERTENSION"], "diabetesType": "TYPE2", "otherConditions": "",
    "allergies": ["البنسلين", "المكسرات"],
    "medications": [{ "name": "وارفارين", "dose": "5 ملغ", "frequency": "مرة يومياً", "isAnticoagulant": true }]
  },
  "turns": [
    { "index": 1, "questionId": "burn.onset", "slot": "onset", "question": "إيمتى صارت الإصابة؟",
      "answer": "قبل حوالي 5 دقايق", "unsure": false }
  ],
  "counters": { "baseAsked": 1, "extraRounds": 0 }
}
```
- `input.text` may be `null` (image-only). `input.images` may be empty (text-only). Never both empty.
- `profile` may be `null` (guest or user disabled it).
- Images: JPEG, ≤1024 px (compressed in the browser), max 3.
- `turns[].unsure: true` means the user pressed "مش متأكد" (answer is `null`).

### 3.2 Response
```json
{
  "status": "needs_answer",
  "case": {
    "type": "thermal_burn",
    "label": "حرق حراري – اليد اليمنى",
    "facts": { "mechanism": "scald", "location": "hand_back_right", "size_vs_palm": "smaller" }
  },
  "confidence": 0.45,
  "missingSlots": ["depth_signs", "airway_signs"],
  "imageFindings": ["احمرار واضح مع فقاعات صغيرة", "المساحة أصغر من كف اليد"],
  "profileFactors": [
    { "label": "سكري – النوع 2", "effect": "يرفع خطر الالتهاب وبطء الشفاء", "severity": "affects" },
    { "label": "وارفارين", "effect": "يؤثر على النزيف واختيار المسكّن", "severity": "important" }
  ],
  "nextQuestion": {
    "id": "burn.location_size", "slot": "location_size",
    "text": "وين بالضبط مكان الحرق، وقديش حجمه مقارنةً بكف إيدك؟",
    "why": "مكان وحجم الحرق بيحددوا درجة الخطر وإذا بتحتاج طوارئ.",
    "isDanger": true, "isExtra": false
  },
  "result": null,
  "emergency": null,
  "audit": { "triggeredRules": [], "sourceIds": [] }
}
```

`status` values and which fields must be present:

| status | `nextQuestion` | `result` | `emergency` |
|---|---|---|---|
| `needs_answer` | required | null | null |
| `completed` | null | required | null |
| `emergency` | null | null | required |

`profileFactors[].severity`: `info | affects | important | allergy`.

### 3.3 `result` (when `status = completed`)
```json
{
  "assessmentLabel": "حرق من الدرجة الثانية (سطحي)",
  "summary": "على ظهر اليد اليمنى، أصغر من نص كف اليد، مع فقاعات صغيرة وإحساس طبيعي بالألم.",
  "riskLevel": "MEDIUM",
  "careDirection": "SEE_DOCTOR_24H",
  "careDirectionReason": "بسبب السكري، المراجعة ضرورية حتى لو تحسّن الحرق.",
  "firstAidSteps": [
    { "text": "برّد الحرق تحت مي جارية فاترة", "duration": "20 دقيقة" },
    { "text": "شيل الخواتم والإسوارة قبل ما تنفخ الإيد", "duration": "فوراً" }
  ],
  "treatments": [
    { "id": "paracetamol", "name": "باراسيتامول", "purpose": "مسكّن للألم",
      "usage": "حسب الجرعة المكتوبة على العبوة عند الحاجة", "suitability": "suitable", "reason": null },
    { "id": "ibuprofen", "name": "إيبوبروفين", "purpose": "مسكّن ومضاد التهاب",
      "usage": "لا يُستخدم", "suitability": "not_suitable", "reason": "بتاخد وارفارين، فبيزيد خطر النزيف" },
    { "id": "topical_antibiotic", "name": "كريم مضاد حيوي موضعي", "purpose": "منع الالتهاب",
      "usage": "فقط إذا وصفه الطبيب", "suitability": "consult_doctor", "reason": "عندك حساسية بنسلين وسكري" }
  ],
  "avoid": ["لا تحط ثلج أو معجون أسنان أو زبدة", "لا تفقع الفقاعات"],
  "goToErIf": ["صعوبة بالتنفس أو دوخة", "الجلد صار أبيض أو أسود أو بدون إحساس"],
  "profileImpacts": ["رفعنا مستوى المتابعة بسبب السكري", "استبعدنا الإيبوبروفين بسبب الوارفارين"],
  "confidence": 0.94,
  "questionsAsked": 7,
  "uncertain": false,
  "sourceIds": ["burn_002"],
  "disclaimer": "هذا تقييم مبدئي وليس تشخيصاً طبياً نهائياً."
}
```
Enums:
- `riskLevel`: `LOW | MEDIUM | HIGH | EMERGENCY`
- `careDirection`: `SELF_CARE | SEE_DOCTOR_24H | URGENT_CARE_NOW | EMERGENCY`
- `suitability`: `suitable | not_suitable | consult_doctor`

### 3.4 `emergency` (when `status = emergency`)
```json
{
  "title": "نزيف مستمر مع تناول مميّع دم",
  "reasons": ["النزيف مستمر أكثر من 10 دقائق رغم الضغط عليه", "بتاخد وارفارين، وهو بيمنع تخثّر الدم"],
  "untilHelp": ["اضغط على الجرح بقوة وبشكل مستمر بقطعة قماش نظيفة", "ارفع الطرف المصاب فوق مستوى القلب إذا أمكن"],
  "avoid": ["لا تشيل القماش عن الجرح لتتفقده", "لا تاخد أسبرين أو إيبوبروفين"],
  "sourceIds": ["bleed_003"]
}
```
(The website adds the paramedic card from the stored profile.)

---

## 4. Behaviour the AI service must guarantee

The website is built on these rules. The mock already behaves this way.

### 4.1 Question flow
1. **5 base questions.** `counters.baseAsked < 5` → return a base question (`isExtra: false`).
2. After 5: if `confidence ≥ 0.85` → `completed`.
3. Else **extra rounds**: 2–3 questions per round (`isExtra: true`) targeting the missing slots, **max 3 rounds**. The website increments `extraRounds` when a round ends; the AI decides round size and signals the last question of a round with `nextQuestion.endsRound: true`.
4. Still < 0.85 after 3 rounds → `completed` with `uncertain: true`, risk raised one level, `careDirection` at least `SEE_DOCTOR_24H`.
5. **Danger questions first.** Never return `completed` while a danger slot is unanswered.
6. **Image-only start** (`input.text = null`): the first questions are intake: what happened, when, where on the body. They count toward the 5.
7. One question per call. Questions are open (the user types the answer). `why` is required.
8. `unsure: true` → that slot stays missing.

### 4.2 Confidence
Must be computed from **slot coverage** (weighted known slots per case type), not from the model's self-rating, so it is stable and explainable. Value in `[0, 1]`.

### 4.3 Safety
- Check red flags on the text, image findings and **every answer** on every call. Any red flag → `status: emergency` immediately.
- Deterministic rules decide emergencies and minimum risk; the LLM may not lower them.
- The profile must raise risk where relevant (e.g. anticoagulant + bleeding or head injury; diabetes + wound/burn → at least `SEE_DOCTOR_24H`; pregnancy + abdominal trauma → emergency; asthma + chemical inhalation → urgent).
- The website also runs its own keyword safety net and will override to emergency if it hits. It never lowers your risk.

### 4.4 Content
- First-aid steps only from a curated, medically reviewed guideline set. Every result lists `sourceIds`.
- Treatments only from a curated over-the-counter catalog. Suitability computed by rules against allergies, conditions, medications, pregnancy and age.
- **No doses, ever.** Use "حسب تعليمات العبوة" or "اسأل الصيدلي". Prescription-only items appear only as `consult_doctor`.
- Use "تقييم مبدئي", never claim a definitive diagnosis.
- Image analysis describes visible findings only; never identify people.

### 4.5 Output quality
- Always valid JSON in exactly this format. If the website can't read the response, the user gets a simple fallback card.
- Keep Arabic short and simple. No markdown in strings.

---

## 5. Testing the integration
1. Run the AI service locally on `:8000`.
2. In `frontend/.env`: `VITE_AI_MODE=remote`, `VITE_AI_SERVICE_URL=http://localhost:8000`.
3. Try the 3 demo scenarios in the website: minor burn by text, image-only bleeding on a warfarin user, unclear fall with extra questions.
