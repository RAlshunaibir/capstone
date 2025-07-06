// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  ME: `${API_BASE_URL}/me`,
  LOGIN: `${API_BASE_URL}/login`,
  SIGNUP: `${API_BASE_URL}/signup`,
  CHAT: `${API_BASE_URL}/chat`,
  CHAT_HISTORY: `${API_BASE_URL}/chat/history`,
  CHAT_HISTORY_BY_SESSION: (sessionId) => `${API_BASE_URL}/chat/history/${sessionId}`,
  DELETE_CHAT_HISTORY: (sessionId) => `${API_BASE_URL}/chat/history/${sessionId}`,
};

export default API_ENDPOINTS; 