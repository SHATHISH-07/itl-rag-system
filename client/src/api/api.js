import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000', 
});

export const uploadFiles = (formData) => api.post('/files/upload-files', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});

export const askQuestion = (query) => api.post('/rag/query', { query });

export default api;