'use client';

import { ChakraProvider, extendTheme } from "@chakra-ui/react";

const theme = extendTheme({
  fonts: {
    heading: "var(--font-geist-sans)",
    body: "var(--font-geist-sans)",
    mono: "var(--font-geist-mono)",
  },
  colors: {
    kai: {
      50: '#E6F7F1',
      100: '#C4EADD',
      200: '#9ADEC9',
      300: '#70D2B4',
      400: '#4FDBA9',
      500: '#33C495',
      600: '#29A07A',
      700: '#1F7C5F',
      800: '#155844',
      900: '#0B3429',
    },
  },
  styles: {
    global: {
      body: {
        bg: 'white',
        color: 'gray.800',
        _dark: {
          bg: 'gray.900',
          color: 'white',
        },
      },
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ChakraProvider theme={theme}>
      {children}
    </ChakraProvider>
  );
} 