import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:5000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const analyzeMeal = async (foods) => {
  try {
    const response = await api.post('/analyze-meal', { foods });
    return response.data;
  } catch (error) {
    if (error.response) {
      throw error.response.data;
    }
    throw { success: false, errors: ['Network error. Is the backend running?'] };
  }
};

export default api;
