'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

interface AccessDeniedProps {
  title?: string;
  message?: string;
  showBackButton?: boolean;
  backTo?: string;
}

/**
 * Component displayed when a user doesn't have permission to access content
 */
export function AccessDenied({
  title = 'Access Denied',
  message = 'You do not have permission to access this resource.',
  showBackButton = true,
  backTo = '/'
}: AccessDeniedProps) {
  const router = useRouter();
  
  const handleGoBack = () => {
    if (backTo) {
      router.push(backTo);
    } else {
      router.back();
    }
  };
  
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8 max-w-md w-full text-center">
        <div className="mb-6">
          <svg 
            className="w-16 h-16 text-red-500 mx-auto" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth="2" 
              d="M12 15v2m0 0v2m0-2h2m-2 0H10m8-9a4 4 0 10-8 0 4 4 0 008 0zM5 15a4 4 0 118 0H5z"
            />
          </svg>
        </div>
        
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          {title}
        </h2>
        
        <p className="text-gray-600 dark:text-gray-300 mb-6">
          {message}
        </p>
        
        {showBackButton && (
          <Button onClick={handleGoBack} className="w-full">
            Go Back
          </Button>
        )}
      </div>
    </div>
  );
} 