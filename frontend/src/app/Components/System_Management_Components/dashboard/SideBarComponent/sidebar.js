'use client';
import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const Sidebar = () => {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    {
      title: 'Dashboard',
      links: [{ href: '/Components/System_Management_Component/dashboard', icon: 'bx bx-home', label: 'Dashboard' }],
    },
    //     {
    //   title: 'Client Portal',
    //   links: [{ href: '/Components/Form_Portal_Management_Component/', icon: 'bx bx-home', label: 'Client Portal' }],
    // },
    {
      title: 'Manage Users',
      links: [
        {  href: '/Components/System_Management_Component/Usermanagement', 
            icon: 'bx bx-user', label: 'View Users' } // Link to /users page
      
  
      ],
      
    },
   
    {
      title: 'Accounts',
      links: [
        { href: '/profile', icon: 'bx bx-user-circle', label: 'Profile' },
        { href: '/logout', icon: 'bx bx-log-out', label: 'Logout' },
      ],
    },
    
  ];

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        className="md:hidden p-4 text-gray-600 z-50 relative"
        onClick={() => setIsOpen(!isOpen)}
      >
        <i className="bx bx-menu text-3xl"></i>
      </button>

      {/* Sidebar */}
      <div className={`fixed top-0 left-0 h-full w-64 bg-white shadow-lg z-40 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 md:relative md:block`}>
        <div className="p-6 space-y-6">
          {navItems.map((section, index) => (
            <div key={index} className="nav-button">
              <span className="font-bold text-primary block mb-2">{section.title}</span>
              <ul className="space-y-2">
                {section.links.map((link, idx) => (
                  <li key={idx}>
                    <Link
                      href={link.href}
                      className={`flex items-center gap-3 px-3 py-2 rounded text-sm hover:bg-gray-100 transition ${pathname === link.href ? 'bg-gray-100 font-semibold' : ''}`}
                    >
                      <i className={`${link.icon} text-xl`} aria-hidden="true"></i>
                      <span>{link.label}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

export default Sidebar;
