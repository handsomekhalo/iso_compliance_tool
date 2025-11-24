"use client";

import { useAuth } from "../../../AuthContext";
import Navbar from "../System_Management_Components/dashboard/SideBarComponent/navheader";
import Sidebar from "../System_Management_Components/dashboard/SideBarComponent/sidebar";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardLayout({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/Components/System_Management_Component/login");
    }
  }, [isAuthenticated, isLoading]);

  if (isLoading) return <p>Checking authentication...</p>;
  if (!isAuthenticated) return null;

  return (
    <div>
      <Navbar />
      <Sidebar />
      <main className="p-6">{children}</main>
    </div>
  );
}
