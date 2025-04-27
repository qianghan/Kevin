import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useColorMode } from '@chakra-ui/react';

interface ColorModeContextType {
  toggleColorMode: () => void;
  setColorMode: (mode: 'light' | 'dark' | 'system') => void;
  colorMode: 'light' | 'dark';
  prefersSystem: boolean;
}

const ColorModeContext = createContext<ColorModeContextType | undefined>(undefined);

interface ColorModeProviderProps {
  children: ReactNode;
}

export const ColorModeProvider = ({ children }: ColorModeProviderProps) => {
  const { colorMode, setColorMode: setChakraColorMode, toggleColorMode: toggleChakraColorMode } = useColorMode();
  const [prefersSystem, setPrefersSystem] = useState(false);
  
  useEffect(() => {
    if (prefersSystem) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      const handleChange = (e: MediaQueryListEvent) => {
        setChakraColorMode(e.matches ? 'dark' : 'light');
      };
      
      // Check initial state
      setChakraColorMode(mediaQuery.matches ? 'dark' : 'light');
      
      // Modern API
      mediaQuery.addEventListener('change', handleChange);
      
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [prefersSystem, setChakraColorMode]);
  
  const contextValue: ColorModeContextType = {
    colorMode,
    toggleColorMode: toggleChakraColorMode,
    setColorMode: (mode) => {
      if (mode === 'system') {
        setPrefersSystem(true);
      } else {
        setPrefersSystem(false);
        setChakraColorMode(mode);
      }
    },
    prefersSystem,
  };
  
  return (
    <ColorModeContext.Provider value={contextValue}>
      {children}
    </ColorModeContext.Provider>
  );
};

export const useKAIColorMode = () => {
  const context = useContext(ColorModeContext);
  if (context === undefined) {
    throw new Error('useKAIColorMode must be used within a ColorModeProvider');
  }
  return context;
}; 