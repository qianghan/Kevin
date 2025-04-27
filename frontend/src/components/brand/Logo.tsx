import React from 'react';
import { Box, BoxProps } from '@chakra-ui/react';

export type LogoSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type LogoVariant = 'full' | 'mark' | 'text';

export interface LogoProps extends Omit<BoxProps, 'size'> {
  size?: LogoSize;
  variant?: LogoVariant;
  showTagline?: boolean;
}

// Size mappings for different logo variants
const sizeMappings = {
  xs: { width: '20px', height: '20px' },
  sm: { width: '24px', height: '24px' },
  md: { width: '32px', height: '32px' },
  lg: { width: '48px', height: '48px' },
  xl: { width: '64px', height: '64px' },
};

const fullSizeMappings = {
  xs: { width: '80px', height: '20px' },
  sm: { width: '96px', height: '24px' },
  md: { width: '128px', height: '32px' },
  lg: { width: '192px', height: '48px' },
  xl: { width: '256px', height: '64px' },
};

/**
 * KAI Logo Component
 * 
 * Renders the KAI logo in different sizes and variants.
 * - size: controls the logo size
 * - variant: 'full' (logo with text), 'mark' (logo only), 'text' (text only)
 * - showTagline: whether to show the tagline (only applies to 'full' variant)
 */
export const Logo: React.FC<LogoProps> = ({ 
  size = 'md', 
  variant = 'full',
  showTagline = false,
  ...rest 
}) => {
  // Since Chakra v3 has a different API, we'll use a simple check for dark mode
  // based on a media query instead of useColorMode
  const isDarkMode = () => {
    if (typeof window !== 'undefined') {
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  };
  
  const isDark = isDarkMode();
  
  // Determine the size dimensions based on variant
  const dimensions = variant === 'full' ? fullSizeMappings[size] : sizeMappings[size];
  
  // Choose the color based on theme
  const logoColor = isDark ? '#4FDBA9' : '#33C495';
  const textColor = isDark ? 'white' : '#0A1723';
  
  // SVG Markup for the KAI logo mark
  const logoMark = (
    <svg 
      viewBox="0 0 32 32" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      width={dimensions.width}
      height={dimensions.height}
    >
      <path
        d="M16 2C8.268 2 2 8.268 2 16s6.268 14 14 14 14-6.268 14-14S23.732 2 16 2zm0 25.2A11.2 11.2 0 0 1 4.8 16 11.2 11.2 0 0 1 16 4.8 11.2 11.2 0 0 1 27.2 16 11.2 11.2 0 0 1 16 27.2z"
        fill={logoColor}
      />
      <path
        d="M16 8.5a7.5 7.5 0 1 0 0 15 7.5 7.5 0 0 0 0-15zm0 12a4.5 4.5 0 1 1 0-9 4.5 4.5 0 0 1 0 9z"
        fill={logoColor}
      />
    </svg>
  );
  
  // SVG Markup for the KAI logo text
  const logoText = (
    <svg 
      viewBox="0 0 80 20" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      width={dimensions.width}
      height={dimensions.height}
    >
      <path
        d="M10.5 2H6v16h4.5v-6.5L17 18h5l-8-8 7.5-8h-5l-6 7.5V2z"
        fill={textColor}
      />
      <path
        d="M41 2h-4.5v16H41V2zM55 2h-4l-8 16h4.5l1.25-2.5h8.5L58.5 18H63L55 2zm-4.75 10l2.75-5.5 2.75 5.5h-5.5z"
        fill={textColor}
      />
      <path
        d="M27 2h-4.5v16H27V2z"
        fill={textColor}
      />
    </svg>
  );
  
  // Tagline component
  const tagline = showTagline && variant === 'full' && (
    <Box 
      as="span"
      fontSize={size === 'xs' ? 'xs' : size === 'sm' ? 'sm' : 'md'}
      fontWeight="light"
      fontStyle="italic"
      color={textColor}
      mt={1}
    >
      Intelligent Conversations
    </Box>
  );
  
  // Render different variants
  if (variant === 'mark') {
    return (
      <Box {...rest}>
        {logoMark}
      </Box>
    );
  }
  
  if (variant === 'text') {
    return (
      <Box {...rest}>
        {logoText}
      </Box>
    );
  }
  
  // Default: full logo (mark + text)
  return (
    <Box display="flex" flexDirection="column" alignItems="flex-start" {...rest}>
      <Box display="flex" alignItems="center">
        <Box marginRight="8px">{logoMark}</Box>
        {logoText}
      </Box>
      {tagline}
    </Box>
  );
};

export default Logo; 