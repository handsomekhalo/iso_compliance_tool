'use client';

  import React from 'react';
  import DashboardPage from '../../DashboardComponents/page';
  import Sidebar from './SideBarComponent/sidebar';
  import Navbar from './SideBarComponent/navheader';

  export default function Dashboard() {
  return (
    
    <div className="flex min-h-screen">
      
      {/* Sidebar on the left */}
      {/* <Sidebar /> */}

      {/* Dashboard content on the right */}
      <div className="flex-1 p-8">
        <Navbar />
        <DashboardPage />
      </div>

    </div>
  );
}

