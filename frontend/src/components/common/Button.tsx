import { Button as ChakraButton, ButtonProps as ChakraButtonProps } from '@chakra-ui/react';
import { ComponentVariant } from '../../theme/theme.types';

export interface ButtonProps extends ChakraButtonProps {
  variant?: ComponentVariant;
}

/**
 * Button component with KAI-specific variants
 */
export const Button = ({ 
  variant = 'primary',
  size = 'md',
  children,
  ...rest
}: ButtonProps) => {
  return (
    <ChakraButton
      variant={variant}
      size={size}
      {...rest}
    >
      {children}
    </ChakraButton>
  );
}; 