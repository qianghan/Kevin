import { ChakraProvider } from '@chakra-ui/react';
import { ReactNode } from 'react';
import { theme } from './index';
import { ColorModeProvider } from './useKAIColorMode';

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider = ({ children }: ThemeProviderProps) => {
  return (
    <ChakraProvider resetCSS theme={theme}>
      <ColorModeProvider>
        {children}
      </ColorModeProvider>
    </ChakraProvider>
  );
}; 