import { Grid as ChakraGrid, GridProps as ChakraGridProps } from '@chakra-ui/react';
import { ReactNode } from 'react';

interface ResponsiveGridProps extends Omit<ChakraGridProps, 'templateColumns'> {
  children: ReactNode;
  columns?: { base?: number; sm?: number; md?: number; lg?: number; xl?: number; '2xl'?: number } | number;
  spacing?: string | { base?: string; sm?: string; md?: string; lg?: string; xl?: string; '2xl'?: string };
}

/**
 * Responsive grid component that adjusts the number of columns based on viewport size
 */
export const ResponsiveGrid = ({ 
  children, 
  columns = { base: 1, md: 2, lg: 3, xl: 4 },
  spacing = { base: '4', md: '6', lg: '8' },
  ...rest 
}: ResponsiveGridProps) => {
  // Convert the columns object to a templateColumns string for each breakpoint
  const templateColumns = typeof columns === 'number'
    ? `repeat(${columns}, 1fr)`
    : {
        base: `repeat(${columns.base || 1}, 1fr)`,
        sm: columns.sm ? `repeat(${columns.sm}, 1fr)` : undefined,
        md: columns.md ? `repeat(${columns.md}, 1fr)` : undefined,
        lg: columns.lg ? `repeat(${columns.lg}, 1fr)` : undefined,
        xl: columns.xl ? `repeat(${columns.xl}, 1fr)` : undefined,
        '2xl': columns['2xl'] ? `repeat(${columns['2xl']}, 1fr)` : undefined,
      };

  return (
    <ChakraGrid
      templateColumns={templateColumns}
      gap={spacing}
      {...rest}
    >
      {children}
    </ChakraGrid>
  );
}; 