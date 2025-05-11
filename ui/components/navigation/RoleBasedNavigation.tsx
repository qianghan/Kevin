'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { usePermissions } from '@/hooks/usePermissions';
import { UserRole } from '@/lib/interfaces/services/user.service';
import { PermissionGuard } from '@/components/permission/PermissionGuard';

interface NavItemProps {
  href: string;
  label: string;
  roles?: UserRole[];
  anyRole?: boolean;
  permissions?: string[];
  anyPermission?: boolean;
}

/**
 * Navigation item with permission-based visibility
 */
function NavItem({ 
  href, 
  label, 
  roles = [], 
  anyRole = true,
  permissions = [],
  anyPermission = true
}: NavItemProps) {
  const pathname = usePathname();
  const isActive = pathname === href;
  
  return (
    <PermissionGuard
      roles={roles}
      anyRole={anyRole}
      permissions={permissions}
      anyPermission={anyPermission}
    >
      <li>
        <Link 
          href={href}
          className={`px-4 py-2 rounded-md text-sm font-medium block transition-colors ${
            isActive 
              ? 'bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-200' 
              : 'text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800'
          }`}
        >
          {label}
        </Link>
      </li>
    </PermissionGuard>
  );
}

interface NavigationSectionProps {
  title: string;
  children: React.ReactNode;
}

/**
 * Navigation section with a title
 */
function NavigationSection({ title, children }: NavigationSectionProps) {
  return (
    <div className="mb-6">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-4">
        {title}
      </h3>
      <ul className="space-y-1">
        {children}
      </ul>
    </div>
  );
}

/**
 * Role-based navigation component
 */
export function RoleBasedNavigation() {
  const [expanded, setExpanded] = useState(true);
  const { hasRole } = usePermissions();
  
  const toggleExpanded = () => {
    setExpanded(!expanded);
  };
  
  return (
    <div className={`bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 ${
      expanded ? 'w-64' : 'w-16'
    } transition-all duration-300 h-screen overflow-y-auto`}>
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
        <div className={`font-bold text-xl ${expanded ? 'block' : 'hidden'}`}>
          Kevin App
        </div>
        <button 
          onClick={toggleExpanded} 
          className="p-1 rounded-md text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          {expanded ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          )}
        </button>
      </div>
      
      {expanded && (
        <nav className="p-4">
          <NavigationSection title="Dashboard">
            <NavItem href="/" label="Overview" />
            <NavItem 
              href="/analytics" 
              label="Analytics" 
              roles={[UserRole.ADMIN, UserRole.TEACHER]} 
            />
          </NavigationSection>
          
          <PermissionGuard roles={[UserRole.ADMIN]}>
            <NavigationSection title="Administration">
              <NavItem 
                href="/admin/users" 
                label="User Management" 
                roles={[UserRole.ADMIN]} 
              />
              <NavItem 
                href="/admin/permissions" 
                label="Permission Management" 
                roles={[UserRole.ADMIN]} 
              />
              <NavItem 
                href="/admin/settings" 
                label="System Settings" 
                roles={[UserRole.ADMIN]} 
              />
            </NavigationSection>
          </PermissionGuard>
          
          <PermissionGuard roles={[UserRole.TEACHER]}>
            <NavigationSection title="Teaching">
              <NavItem 
                href="/teaching/courses" 
                label="My Courses" 
                roles={[UserRole.TEACHER]} 
              />
              <NavItem 
                href="/teaching/assignments" 
                label="Assignments" 
                roles={[UserRole.TEACHER]} 
              />
              <NavItem 
                href="/teaching/gradebook" 
                label="Gradebook" 
                roles={[UserRole.TEACHER]} 
              />
            </NavigationSection>
          </PermissionGuard>
          
          <PermissionGuard roles={[UserRole.STUDENT]}>
            <NavigationSection title="Learning">
              <NavItem 
                href="/learning/dashboard" 
                label="Learning Dashboard" 
                roles={[UserRole.STUDENT]} 
              />
              <NavItem 
                href="/learning/courses" 
                label="My Courses" 
                roles={[UserRole.STUDENT]} 
              />
              <NavItem 
                href="/learning/progress" 
                label="My Progress" 
                roles={[UserRole.STUDENT]} 
              />
            </NavigationSection>
          </PermissionGuard>
          
          <NavigationSection title="Account">
            <NavItem href="/profile" label="My Profile" />
            <NavItem href="/preferences" label="Preferences" />
          </NavigationSection>
        </nav>
      )}
      
      {/* Collapsed navigation */}
      {!expanded && (
        <nav className="p-4">
          <ul className="space-y-4">
            <li>
              <Link href="/" className="flex justify-center p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </Link>
            </li>
            
            <PermissionGuard roles={[UserRole.ADMIN]}>
              <li>
                <Link href="/admin/permissions" className="flex justify-center p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                  </svg>
                </Link>
              </li>
            </PermissionGuard>
            
            <PermissionGuard roles={[UserRole.TEACHER]}>
              <li>
                <Link href="/teaching/courses" className="flex justify-center p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path d="M12 14l9-5-9-5-9 5 9 5z" />
                    <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
                  </svg>
                </Link>
              </li>
            </PermissionGuard>
            
            <PermissionGuard roles={[UserRole.STUDENT]}>
              <li>
                <Link href="/learning/dashboard" className="flex justify-center p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </Link>
              </li>
            </PermissionGuard>
            
            <li>
              <Link href="/profile" className="flex justify-center p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </Link>
            </li>
          </ul>
        </nav>
      )}
    </div>
  );
} 