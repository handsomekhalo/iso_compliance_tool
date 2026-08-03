'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [authToken, setAuthToken] = useState(null);
  const [csrfToken, setCSRFToken] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Load tokens + user after mount (client-side only)
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    const csrf = localStorage.getItem('csrfToken');
    const storedUser = localStorage.getItem('user');

    if (token && token !== 'null') setAuthToken(token);
    if (csrf && csrf !== 'null') setCSRFToken(csrf);
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        setUser(null);
      }
    }

    setIsLoading(false);
  }, []);

  /**
   * login({ token, csrf, user })
   * `user` is expected to be { email, role, bank, ... } — role drives
   * sidebar/nav visibility. csrf is optional (not needed once real token
   * auth is wired up, kept for the current CSRF+Token backend flow).
   */
  const login = ({ token, csrf, user: userData }) => {
    if (!token || token === 'null') return;

    setAuthToken(token);
    setCSRFToken(csrf || null);
    setUser(userData || null);

    localStorage.setItem('authToken', token);
    localStorage.setItem('csrfToken', csrf || '');
    if (userData) localStorage.setItem('user', JSON.stringify(userData));
  };

  const logout = () => {
    setAuthToken(null);
    setCSRFToken(null);
    setUser(null);
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
    user,
    role: user?.role ?? null,
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


// 'use client';

// import React, { createContext, useContext, useState, useEffect } from 'react';
// import { useRouter } from 'next/navigation';

// const AuthContext = createContext();

// export const useAuth = () => useContext(AuthContext);

// export const AuthProvider = ({ children }) => {
//   const [authToken, setAuthToken] = useState(null);
//   const [csrfToken, setCSRFToken] = useState(null);
//   const [isLoading, setIsLoading] = useState(true);
//   const router = useRouter();

//   // Load tokens after mount (client-side only)
//   useEffect(() => {
//     const token = localStorage.getItem('authToken');
//     const csrf = localStorage.getItem('csrfToken');

//     if (token && token !== 'null') setAuthToken(token);
//     if (csrf && csrf !== 'null') setCSRFToken(csrf);

//     setIsLoading(false);
//   }, []);

//   const login = (token, csrf) => {
//     if (!token || token === 'null') return;

//     setAuthToken(token);
//     setCSRFToken(csrf || null);
//     localStorage.setItem('authToken', token);
//     localStorage.setItem('csrfToken', csrf || '');
//   };

//   const logout = () => {
//     setAuthToken(null);
//     setCSRFToken(null);
//     localStorage.removeItem('authToken');
//     localStorage.removeItem('csrfToken');
//     localStorage.removeItem('user');
//     router.push('/');
//   };

//   const navigate = (path) => {
//     router.push(path);
//   };

//   const isAuthenticated = !!authToken && authToken !== 'null';

//   const contextValue = {
//     authToken,
//     csrfToken,
//     isAuthenticated,
//     isLoading,
//     login,
//     logout,
//     navigate,
//   };

//   return (
//     <AuthContext.Provider value={contextValue}>
//       {children}
//     </AuthContext.Provider>
//   );
// };