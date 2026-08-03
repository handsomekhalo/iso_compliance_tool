'use client';

import { useState } from 'react';
// import LoginPage from './Login_Component/login';
import LoginPage from '../../Login_Component/login';
import RegisterPage from '../Components/Register/RegisterComponent';


// import RegisterPage from './Register_Component/register';// import Dashboard from './Components/System_Management_Component/dashboard/dashboard';
export default function Home() {
  const [showLogin, setShowLogin] = useState(true);

  const togglePage = () => setShowLogin(!showLogin);

  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start">
        {showLogin ? (
          <>
            <LoginPage />
            <p className="text-sm mt-4">
              Don’t have an account?{' '}
              <button
                onClick={togglePage}
                className="text-indigo-600 hover:underline"
              >
                Register
              </button>
            </p>
          </>
        ) : (
          <>
            <RegisterPage />
            <p className="text-sm mt-4">
              Already have an account?{' '}
              <button
                onClick={togglePage}
                className="text-indigo-600 hover:underline"
              >
                Login
              </button>
            </p>
          </>
        )}

     

      </main>
    </div>
  );
}
