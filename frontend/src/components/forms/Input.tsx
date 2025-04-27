import {
  Input as ChakraInput,
  InputProps as ChakraInputProps,
  FormControl,
  FormLabel,
  FormErrorMessage,
  FormHelperText,
} from '@chakra-ui/react';

export interface InputProps extends Omit<ChakraInputProps, 'size'> {
  name: string;
  label?: string;
  helperText?: string;
  errorMessage?: string;
  isRequired?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Form Input component with integrated label, helper text, and error state
 */
export const Input = ({
  name,
  label,
  helperText,
  errorMessage,
  isRequired = false,
  size = 'md',
  ...rest
}: InputProps) => {
  const hasError = !!errorMessage;
  
  return (
    <FormControl id={name} isInvalid={hasError} isRequired={isRequired}>
      {label && <FormLabel>{label}</FormLabel>}
      <ChakraInput
        name={name}
        size={size}
        variant="filled"
        bg="background.lightHover"
        _hover={{ bg: 'background.lightActive' }}
        _dark={{
          bg: 'whiteAlpha.50',
          _hover: { bg: 'whiteAlpha.100' },
        }}
        {...rest}
      />
      {helperText && !hasError && (
        <FormHelperText>{helperText}</FormHelperText>
      )}
      {hasError && <FormErrorMessage>{errorMessage}</FormErrorMessage>}
    </FormControl>
  );
}; 