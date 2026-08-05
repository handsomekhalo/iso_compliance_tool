'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../AuthContext';
import Sidebar from '../../components/sidebar';
import Navbar from '../../components/navheader';

export default function DashboardLayout({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading…</div>;
  }

  if (!isAuthenticated) {
    return null; // redirect in flight
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1">
        <Navbar />
        <main className="px-6 pb-10">{children}</main>
      </div>
    </div>
  );
}

// "use client";

// import { useAuth } from "../../../../AuthContext";
// import Navbar from "../System_Management_Components/dashboard/SideBarComponent/navheader";
// import Sidebar from "../System_Management_Components/dashboard/SideBarComponent/sidebar";
// import { useRouter } from "next/navigation";
// import { useEffect } from "react";

// export default function DashboardLayout({ children }) {
//   const { isAuthenticated, isLoading } = useAuth();
//   const router = useRouter();

//   useEffect(() => {
//     if (!isLoading && !isAuthenticated) {
//       router.push("/dashboard");
//     }
//   }, [isAuthenticated, isLoading]);

//   if (isLoading) return <p>Checking authentication...</p>;
//   if (!isAuthenticated) return null;

//   return (
//     <div>
//       <Navbar />
//       <Sidebar />
//       <main className="p-6">{children}</main>
//     </div>
//   );
// }
