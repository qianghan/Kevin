/**
 * PullToRefresh Component
 * 
 * A component that adds pull-to-refresh functionality to scrollable content.
 * Follows single responsibility principle by focusing only on pull-to-refresh interaction.
 */

import React, { ReactNode } from 'react';
import { Box, Spinner, Text, useColorModeValue, BoxProps } from '@chakra-ui/react';
import { usePullToRefresh } from '../../hooks/gestures/usePullToRefresh';
import { keyframes } from '../../theme/animations';

interface PullToRefreshProps extends Omit<BoxProps, 'onRefresh'> {
  /** Child elements to render inside the scrollable container */
  children: ReactNode;
  /** Callback function executed when refresh is triggered */
  onRefresh: () => Promise<any> | void;
  /** Text to display when pulling down */
  pullText?: string;
  /** Text to display when refreshing */
  refreshingText?: string;
  /** Distance in pixels required to trigger refresh */
  threshold?: number;
  /** Maximum distance the user can pull down */
  maxPullDistance?: number;
  /** Whether to show the loading spinner */
  showSpinner?: boolean;
  /** Whether to show text instructions */
  showText?: boolean;
  /** Height of the container (default: 100%) */
  height?: string | number;
  /** Width of the container (default: 100%) */
  width?: string | number;
  /** Custom indicator component to render instead of the default */
  customIndicator?: (state: { isPulling: boolean; isRefreshing: boolean; progress: number }) => ReactNode;
}

/**
 * PullToRefresh component adds pull-to-refresh functionality to scrollable containers
 * 
 * @example
 * ```tsx
 * <PullToRefresh onRefresh={async () => await fetchNewData()}>
 *   <Box>
 *     {items.map(item => (
 *       <ListItem key={item.id} data={item} />
 *     ))}
 *   </Box>
 * </PullToRefresh>
 * ```
 */
export const PullToRefresh: React.FC<PullToRefreshProps> = ({
  children,
  onRefresh,
  pullText = 'Pull down to refresh',
  refreshingText = 'Refreshing...',
  threshold = 80,
  maxPullDistance = 120,
  showSpinner = true,
  showText = true,
  height = '100%',
  width = '100%',
  customIndicator,
  ...rest
}) => {
  // Use the pull-to-refresh hook
  const { 
    containerRef, 
    contentRef, 
    state, 
    indicatorStyle, 
    contentStyle 
  } = usePullToRefresh({
    onRefresh,
    threshold,
    maxPullDistance,
  });

  // Calculate colors
  const bgColor = useColorModeValue('gray.100', 'gray.700');
  const textColor = useColorModeValue('gray.600', 'gray.200');
  const spinnerColor = useColorModeValue('kai.500', 'kai.200');

  // Define spin animation
  const spin = keyframes.spin;

  return (
    <Box
      ref={containerRef as React.RefObject<HTMLDivElement>}
      height={height}
      width={width}
      overflow="auto"
      position="relative"
      {...rest}
    >
      <Box
        ref={contentRef as React.RefObject<HTMLDivElement>}
        style={contentStyle}
        minHeight="100%"
        width="100%"
      >
        {/* Indicator */}
        {(state.isPulling || state.isRefreshing) && (
          <Box
            style={indicatorStyle}
            height="60px"
            bg={bgColor}
            borderBottomRadius="md"
          >
            {customIndicator ? (
              customIndicator(state)
            ) : (
              <Box 
                display="flex" 
                alignItems="center" 
                justifyContent="center" 
                height="100%"
                opacity={state.progress}
              >
                {showSpinner && (
                  <Spinner
                    color={spinnerColor}
                    size="sm"
                    mr={2}
                    animation={`${spin} 1s linear infinite`}
                    speed={state.isRefreshing ? '0.8s' : `${1.5 - state.progress}s`}
                  />
                )}
                {showText && (
                  <Text color={textColor} fontSize="sm" fontWeight="medium">
                    {state.isRefreshing ? refreshingText : pullText}
                  </Text>
                )}
              </Box>
            )}
          </Box>
        )}

        {/* Content */}
        {children}
      </Box>
    </Box>
  );
};

/**
 * Simplified version with just the behavior
 */
export const usePullToRefreshBehavior = usePullToRefresh; 