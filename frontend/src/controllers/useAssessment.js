import { useState, useCallback } from 'react';
import * as assessmentModel from '../models/assessmentModel';
import * as profileModel from '../models/profileModel';
import ai from '../services/ai';
import { useAuth } from './AuthContext';

export function useAssessment(existingId = null) {
  const { user } = useAuth();
  const [assessment, setAssessment] = useState(() =>
    existingId ? assessmentModel.get(existingId) : null
  );
  const [loading, setLoading] = useState(false);

  async function runStep(data) {
    setLoading(true);
    try {
      const profile = user ? profileModel.get(user.id) : null;
      const current = assessmentModel.get(data.id);

      const request = {
        lang: 'ar',
        input: { text: current.text, images: current.images || [] },
        profile,
        turns: current.turns || [],
        counters: {
          baseAsked: current.baseAsked || 0,
          extraRounds: current.extraRounds || 0,
        },
        _assessmentId: data.id,
      };

      const res = await ai.assessStep(request);

      if (res.status === 'emergency') {
        const updated = assessmentModel.update(data.id, {
          status: 'EMERGENCY',
          caseLabel: res.case?.label,
          confidence: res.confidence,
          imageFindings: res.imageFindings || [],
          profileFactors: res.profileFactors || [],
          emergency: res.emergency,
        });
        setAssessment(updated);
      } else if (res.status === 'completed') {
        assessmentModel.removeImages(data.id);
        const updated = assessmentModel.update(data.id, {
          status: 'COMPLETED',
          caseLabel: res.case?.label,
          confidence: res.confidence,
          imageFindings: res.imageFindings || [],
          profileFactors: res.profileFactors || [],
          result: res.result,
        });
        setAssessment(updated);
      } else {
        const updated = assessmentModel.update(data.id, {
          status: 'QUESTIONING',
          caseLabel: res.case?.label,
          confidence: res.confidence,
          imageFindings: res.imageFindings || [],
          profileFactors: res.profileFactors || [],
          currentQuestion: res.nextQuestion,
        });
        setAssessment(updated);
      }
    } catch {
      const updated = assessmentModel.update(data.id, {
        status: 'FAILED',
      });
      setAssessment(updated);
    } finally {
      setLoading(false);
    }
  }

  const start = useCallback(async ({ text, images }) => {
    const a = assessmentModel.create({
      id: crypto.randomUUID(),
      userId: user?.id,
      createdAt: new Date().toISOString(),
      status: 'QUESTIONING',
      text,
      images: images || [],
      caseLabel: null,
      confidence: 0,
      baseAsked: 0,
      extraRounds: 0,
      imageFindings: [],
      profileFactors: [],
      turns: [],
      currentQuestion: null,
      result: null,
      emergency: null,
    });
    setAssessment(a);
    await runStep(a);
    return a.id;
  }, [user]);

  const answer = useCallback(async ({ answer: answerText, unsure }) => {
    if (!assessment) return;

    const q = assessment.currentQuestion;
    const newTurn = {
      index: (assessment.turns?.length || 0) + 1,
      questionId: q.id,
      slot: q.slot,
      question: q.text,
      why: q.why,
      isDanger: q.isDanger,
      isExtra: q.isExtra,
      endsRound: q.endsRound || false,
      answer: unsure ? null : answerText,
      unsure: !!unsure,
    };

    let newBaseAsked = assessment.baseAsked || 0;
    let newExtraRounds = assessment.extraRounds || 0;
    if (!q.isExtra) newBaseAsked++;
    if (q.endsRound) newExtraRounds++;

    const updated = assessmentModel.update(assessment.id, {
      turns: [...(assessment.turns || []), newTurn],
      baseAsked: newBaseAsked,
      extraRounds: newExtraRounds,
      currentQuestion: null,
    });
    setAssessment(updated);
    await runStep(updated);
  }, [assessment]);

  const goBack = useCallback(() => {
    if (!assessment || !assessment.turns?.length) return;
    const newTurns = assessment.turns.slice(0, -1);
    const lastTurn = assessment.turns[assessment.turns.length - 1];

    let newBaseAsked = assessment.baseAsked || 0;
    let newExtraRounds = assessment.extraRounds || 0;
    if (!lastTurn.isExtra) newBaseAsked = Math.max(0, newBaseAsked - 1);
    if (lastTurn.endsRound) newExtraRounds = Math.max(0, newExtraRounds - 1);

    const updated = assessmentModel.update(assessment.id, {
      turns: newTurns,
      baseAsked: newBaseAsked,
      extraRounds: newExtraRounds,
      currentQuestion: {
        id: lastTurn.questionId,
        slot: lastTurn.slot,
        text: lastTurn.question,
        why: lastTurn.why,
        isDanger: lastTurn.isDanger,
        isExtra: lastTurn.isExtra,
        endsRound: lastTurn.endsRound,
      },
      status: 'QUESTIONING',
      result: null,
      emergency: null,
    });
    setAssessment(updated);
  }, [assessment]);

  return { assessment, loading, start, answer, goBack };
}
