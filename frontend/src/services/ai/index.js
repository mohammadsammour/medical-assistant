import * as mock from './mockAi';
import * as remote from './remoteAi';

const ai = {
  // Symptom assessments always use the backend's questions and urgency decisions.
  assessStep: remote.assessStep,
  extractProfile: import.meta.env.VITE_AI_MODE === 'remote'
    ? remote.extractProfile
    : mock.extractProfile,
};

export default ai;
