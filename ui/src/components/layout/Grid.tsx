/**
 * Grid Layout Components
 * 
 * Responsive grid layouts that adapt to different viewport sizes.
 * Follows single responsibility principle by focusing only on layout.
 */

import React from 'react';
import { Box, BoxProps, SimpleGrid, SimpleGridProps, Flex, FlexProps } from '@chakra-ui/react';

/**
 * Responsive grid configuration by breakpoint
 */
export type ResponsiveValue<T> = T | { base?: T; sm?: T; md?: T; lg?: T; xl?: T; '2xl'?: T };

/**
 * Properties for the ResponsiveGrid component
 */
export interface ResponsiveGridProps extends Omit<SimpleGridProps, 'columns'> {
  /** Number of columns at different breakpoints */
  columns: ResponsiveValue<number>;
  /** Gap between grid items at different breakpoints */
  spacing?: ResponsiveValue<string | number>;
  /** Whether to automatically adjust row height to match the tallest item */
  autoRows?: boolean;
  /** Optional minimum child width that will take precedence over columns */
  minChildWidth?: ResponsiveValue<string>;
  /** Children to render in the grid */
  children: React.ReactNode;
}

/**
 * A responsive grid layout that adapts to different viewport sizes
 * 
 * @example
 * ```tsx
 * <ResponsiveGrid columns={{ base: 1, md: 2, lg: 3 }} spacing="4">
 *   <Card>Item 1</Card>
 *   <Card>Item 2</Card>
 *   <Card>Item 3</Card>
 * </ResponsiveGrid>
 * ```
 */
export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  columns,
  spacing = 4,
  autoRows = false,
  minChildWidth,
  children,
  ...rest
}) => {
  return (
    <SimpleGrid
      columns={columns}
      spacing={spacing}
      minChildWidth={minChildWidth}
      {...(autoRows && { gridAutoRows: '1fr' })}
      {...rest}
    >
      {children}
    </SimpleGrid>
  );
};

/**
 * Properties for the MasonryGrid component
 */
export interface MasonryGridProps extends Omit<BoxProps, 'children'> {
  /** Number of columns at different breakpoints */
  columns: ResponsiveValue<number>;
  /** Gap between grid items */
  spacing?: ResponsiveValue<string | number>;
  /** Children to render in the masonry layout */
  children: React.ReactNode[];
}

/**
 * A masonry grid layout with variable height items
 * 
 * @example
 * ```tsx
 * <MasonryGrid columns={{ base: 1, md: 2, lg: 3 }} spacing="4">
 *   <Card height="200px">Item 1</Card>
 *   <Card height="150px">Item 2</Card>
 *   <Card height="300px">Item 3</Card>
 * </MasonryGrid>
 * ```
 */
export const MasonryGrid: React.FC<MasonryGridProps> = ({
  columns,
  spacing = 4,
  children,
  ...rest
}) => {
  // Convert responsive columns to a consistent object format
  const columnObj = typeof columns === 'object' 
    ? columns 
    : { base: columns };
  
  // Calculate normalized column definition
  const columnDef = {
    base: columnObj.base || 1,
    sm: columnObj.sm || columnObj.base || 1,
    md: columnObj.md || columnObj.sm || columnObj.base || 2,
    lg: columnObj.lg || columnObj.md || columnObj.sm || columnObj.base || 3,
    xl: columnObj.xl || columnObj.lg || columnObj.md || columnObj.sm || columnObj.base || 4,
    '2xl': columnObj['2xl'] || columnObj.xl || columnObj.lg || columnObj.md || columnObj.sm || columnObj.base || 4,
  };

  // Helper to distribute children into columns
  const distributeChildrenIntoColumns = () => {
    const columnValues = [1, 1, 2, 3, 4, 4]; // Default values for [base, sm, md, lg, xl, 2xl]
    const breakpoints = ['base', 'sm', 'md', 'lg', 'xl', '2xl'] as const;
    
    // Get current breakpoint column count for SSR safety
    let currentColumns = 1;
    for (let i = breakpoints.length - 1; i >= 0; i--) {
      const bp = breakpoints[i];
      if (columnDef[bp]) {
        currentColumns = columnDef[bp] as number;
        break;
      }
    }

    // Ensure we have a valid number of columns
    currentColumns = Math.max(1, currentColumns);
    
    // Prepare column arrays
    const columns: React.ReactNode[][] = Array.from({ length: currentColumns }, () => []);
    
    // Distribute children among columns (using a naive approach for SSR compatibility)
    // For a real-world implementation, we'd use a height-aware distribution with useEffect
    React.Children.forEach(children, (child, index) => {
      const columnIndex = index % currentColumns;
      columns[columnIndex].push(child);
    });

    return columns;
  };

  return (
    <Flex wrap="wrap" gap={spacing} {...rest}>
      {distributeChildrenIntoColumns().map((columnChildren, colIndex) => (
        <Box
          key={colIndex}
          flex={{
            base: columnDef.base === 1 ? '0 0 100%' : `0 0 calc(${100 / columnDef.base}% - ${typeof spacing === 'number' ? spacing : 4}px)`,
            sm: columnDef.sm === 1 ? '0 0 100%' : `0 0 calc(${100 / columnDef.sm}% - ${typeof spacing === 'number' ? spacing : 4}px)`,
            md: columnDef.md === 1 ? '0 0 100%' : `0 0 calc(${100 / columnDef.md}% - ${typeof spacing === 'number' ? spacing : 4}px)`,
            lg: columnDef.lg === 1 ? '0 0 100%' : `0 0 calc(${100 / columnDef.lg}% - ${typeof spacing === 'number' ? spacing : 4}px)`,
            xl: columnDef.xl === 1 ? '0 0 100%' : `0 0 calc(${100 / columnDef.xl}% - ${typeof spacing === 'number' ? spacing : 4}px)`,
            '2xl': columnDef['2xl'] === 1 ? '0 0 100%' : `0 0 calc(${100 / columnDef['2xl']}% - ${typeof spacing === 'number' ? spacing : 4}px)`,
          }}
          display="flex"
          flexDirection="column"
          gap={spacing}
        >
          {columnChildren}
        </Box>
      ))}
    </Flex>
  );
};

/**
 * Properties for the AutoGrid component
 */
export interface AutoGridProps extends Omit<BoxProps, 'children'> {
  /** Minimum width for each grid item */
  minItemWidth?: string;
  /** Gap between grid items */
  spacing?: ResponsiveValue<string | number>;
  /** Children to render in the grid */
  children: React.ReactNode;
}

/**
 * An auto-sizing grid that fits as many items as possible based on minimum width
 * 
 * @example
 * ```tsx
 * <AutoGrid minItemWidth="250px" spacing="4">
 *   <Card>Item 1</Card>
 *   <Card>Item 2</Card>
 *   <Card>Item 3</Card>
 * </AutoGrid>
 * ```
 */
export const AutoGrid: React.FC<AutoGridProps> = ({
  minItemWidth = '250px',
  spacing = 4,
  children,
  ...rest
}) => {
  return (
    <Box
      display="grid"
      gridTemplateColumns={`repeat(auto-fill, minmax(${minItemWidth}, 1fr))`}
      gridGap={spacing}
      {...rest}
    >
      {children}
    </Box>
  );
};

/**
 * Properties for the TwoColumnLayout component
 */
export interface TwoColumnLayoutProps extends FlexProps {
  /** Width of the sidebar at different breakpoints */
  sidebarWidth?: ResponsiveValue<string | number>;
  /** Whether the sidebar is on the left or right */
  sidebarPosition?: 'left' | 'right';
  /** Content for the sidebar */
  sidebar: React.ReactNode;
  /** Main content */
  children: React.ReactNode;
  /** Gap between sidebar and main content */
  spacing?: ResponsiveValue<string | number>;
  /** Whether to stack layout on mobile devices */
  stackOnMobile?: boolean;
}

/**
 * A two-column layout with a main content area and a sidebar
 * 
 * @example
 * ```tsx
 * <TwoColumnLayout 
 *   sidebar={<Sidebar />} 
 *   sidebarWidth={{ base: '100%', md: '300px' }}
 *   stackOnMobile
 * >
 *   <MainContent />
 * </TwoColumnLayout>
 * ```
 */
export const TwoColumnLayout: React.FC<TwoColumnLayoutProps> = ({
  sidebarWidth = { base: '100%', md: '250px' },
  sidebarPosition = 'left',
  sidebar,
  children,
  spacing = 4,
  stackOnMobile = true,
  ...rest
}) => {
  return (
    <Flex
      direction={stackOnMobile ? { base: 'column', md: 'row' } : 'row'}
      gap={spacing}
      {...rest}
    >
      {sidebarPosition === 'left' ? (
        <>
          <Box width={sidebarWidth} flex="0 0 auto">
            {sidebar}
          </Box>
          <Box flex="1 1 auto">{children}</Box>
        </>
      ) : (
        <>
          <Box flex="1 1 auto">{children}</Box>
          <Box width={sidebarWidth} flex="0 0 auto">
            {sidebar}
          </Box>
        </>
      )}
    </Flex>
  );
}; 