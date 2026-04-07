import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000', 
});

export const uploadFiles = (formData) => api.post('/files/upload-files', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});

export const getFiles = () => api.get('/files/list-files');


export const askQuestion = (query, filterKeyword = null, currentTopK) => {
  return api.post('/rag/query', { 
    query: query,
    filter_keyword: filterKeyword,
    top_k: currentTopK
  });
};

export default api;