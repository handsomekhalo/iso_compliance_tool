"use client"; // Ensure this is a client component

import axios from 'axios';

// Create an Axios instance with a predefined configuration
const backendApi = axios.create({
  // baseURL:'http://3.144.218.251',
 
  baseURL: "http://127.0.0.1:8000",
    // 👈 Public IP of your EC2 instance
  withCredentials: true,          // Ensures cookies (like CSRF token) are sent
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add Authorization token
backendApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (optional for global error handling)
backendApi.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
);

export default backendApi;
