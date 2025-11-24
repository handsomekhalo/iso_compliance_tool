
'use client';
import { useEffect } from 'react';
import { useAuth } from '../../../AuthContext';
import { useRouter } from 'next/navigation';
// import backendApi from '../../../utils/backendApi';
import backendApi from '../../utils/backendApi';
import Sidebar from '../Components/System_Management_Components/dashboard/SideBarComponent/sidebar';
import Navbar from '../Components/System_Management_Components/dashboard/SideBarComponent/navheader';
// import Sidebar from '../Components/System_Management_Component/dashboard/SideBarComponent/sidebar';
// import Navbar from '../System_Management_Component/dashboard/SideBarComponent/navheader';

export default function LogoutPage() {
  const { authToken, csrfToken, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const performLogout = async () => {
      try {
        await backendApi.post(
          '/system_management/logout/',
          {},
          {
            headers: {
              Authorization: `Token ${authToken}`,
              'X-CSRFToken': csrfToken,
              'Content-Type': 'application/json',
            },
            withCredentials: true,
          }
        );
      } catch (err) {
        console.error('Logout failed:', err);
      } finally {
        logout();
        router.push('/');
      }
    };

    performLogout();
  }, [authToken, csrfToken, logout, router]);

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Navbar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-lg text-gray-600">Logging you out...</p>
        </main>
      </div>
    </div>
  );
}
