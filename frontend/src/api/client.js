import axios from 'axios';

const api = axios.create({
  baseURL: 'https://nutrisense-yonc.onrender.com',
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
    throw { success: false, errors: ['Network error. Backend may be sleeping or unreachable.'] };
  }
};

export default api;