'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [authToken, setAuthToken] = useState(null);
  const [csrfToken, setCSRFToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Load tokens after mount (client-side only)
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    const csrf = localStorage.getItem('csrfToken');

    if (token && token !== 'null') setAuthToken(token);
    if (csrf && csrf !== 'null') setCSRFToken(csrf);

    setIsLoading(false);
  }, []);

  const login = (token, csrf) => {
    if (!token || token === 'null') return;

    setAuthToken(token);
    setCSRFToken(csrf || null);
    localStorage.setItem('authToken', token);
    localStorage.setItem('csrfToken', csrf || '');
  };

  const logout = () => {
    setAuthToken(null);
    setCSRFToken(null);
    localStorage.removeItem('authToken');
    localStorage.removeItem('csrfToken');
    localStorage.removeItem('user');
    router.push('/');
  };

  const navigate = (path) => {
    router.push(path);
  };

  const isAuthenticated = !!authToken && authToken !== 'null';

  const contextValue = {
    authToken,
    csrfToken,
    isAuthenticated,
    isLoading,
    login,
    logout,
    navigate,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};