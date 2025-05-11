'use client';

import { useMemo } from 'react';

interface PasswordStrengthProps {
  password: string;
}

export function PasswordStrength({ password }: PasswordStrengthProps) {
  const strength = useMemo(() => calculatePasswordStrength(password), [password]);
  
  const getStrengthLabel = () => {
    if (!password) return 'None';
    if (strength < 30) return 'Weak';
    if (strength < 60) return 'Medium';
    if (strength < 80) return 'Strong';
    return 'Very Strong';
  };
  
  const getStrengthColor = () => {
    if (!password) return 'bg-gray-200';
    if (strength < 30) return 'bg-red-500';
    if (strength < 60) return 'bg-yellow-500';
    if (strength < 80) return 'bg-green-500';
    return 'bg-blue-500';
  };

  return (
    <div className="mt-1">
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={`h-full ${getStrengthColor()} transition-all duration-300`}
          style={{ width: `${Math.max(5, strength)}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-xs text-gray-500">
        <span>Strength:</span>
        <span>{getStrengthLabel()}</span>
      </div>
    </div>
  );
}

// Function to calculate password strength as a percentage (0-100)
function calculatePasswordStrength(password: string): number {
  if (!password) return 0;
  
  let score = 0;
  const length = password.length;
  
  // Length check
  if (length > 4) score += 10;
  if (length > 7) score += 10;
  if (length > 11) score += 10;
  
  // Character variety checks
  const hasLowercase = /[a-z]/.test(password);
  const hasUppercase = /[A-Z]/.test(password);
  const hasNumbers = /\d/.test(password);
  const hasSpecialChars = /[^a-zA-Z0-9]/.test(password);
  
  if (hasLowercase) score += 10;
  if (hasUppercase) score += 15;
  if (hasNumbers) score += 15;
  if (hasSpecialChars) score += 20;
  
  // Bonus for combination of character types
  const varietyCount = [hasLowercase, hasUppercase, hasNumbers, hasSpecialChars].filter(Boolean).length;
  score += (varietyCount - 1) * 5;
  
  // Check for common patterns
  if (/123|abc|qwerty|password|admin|welcome/i.test(password)) {
    score -= 20;
  }
  
  // Normalize score between 0-100
  return Math.max(0, Math.min(100, score));
} 