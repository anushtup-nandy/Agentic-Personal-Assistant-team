import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// User Profile API
export const profileApi = {
    create: (data) => api.post('/profiles', data),
    get: (id) => api.get(`/profiles/${id}`),
    getByEmail: (email) => api.get(`/profiles/by-email/${email}`),
    list: () => api.get('/profiles'),
};

// Document API
export const documentApi = {
    upload: (profileId, file) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post(`/profiles/${profileId}/documents`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
    list: (profileId) => api.get(`/profiles/${profileId}/documents`),
    delete: (documentId) => api.delete(`/documents/${documentId}`),
    generateSummary: (profileId) => api.post(`/profiles/${profileId}/generate-summary`),
};

// Agent API
export const agentApi = {
    create: (profileId, data) => api.post(`/profiles/${profileId}/agents`, data),
    list: (profileId, activeOnly = false) =>
        api.get(`/profiles/${profileId}/agents`, { params: { active_only: activeOnly } }),
    get: (id) => api.get(`/agents/${id}`),
    update: (id, data) => api.patch(`/agents/${id}`, data),
    delete: (id) => api.delete(`/agents/${id}`),
};

// Debate API
export const debateApi = {
    create: (profileId, data) => api.post(`/profiles/${profileId}/debates`, data),
    get: (sessionId) => api.get(`/debates/${sessionId}`),
    list: (profileId) => api.get(`/profiles/${profileId}/debates`),
    delete: (sessionId) => api.delete(`/debates/${sessionId}`),
    start: (sessionId) => `/api/debates/${sessionId}/start`, // Returns URL for SSE
};

// Utility API
export const utilityApi = {
    validatePrompt: (rawPrompt) => api.post('/validate-prompt', { raw_prompt: rawPrompt }),
    getTemplate: () => api.get('/prompt-template'),
    health: () => api.get('/health'),
};

export default api;
