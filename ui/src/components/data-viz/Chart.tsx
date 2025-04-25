import React from 'react';
import { Box, Text, Flex, VStack, HStack, Divider, useTheme } from '@chakra-ui/react';

export interface ChartProps {
  /**
   * Chart title
   */
  title?: string;
  /**
   * Chart description or subtitle
   */
  description?: string;
  /**
   * Data to visualize - format depends on chart type
   */
  data: any[];
  /**
   * Chart dimensions
   */
  dimensions?: {
    width?: number | string;
    height?: number | string;
  };
  /**
   * Chart legend configuration
   */
  legend?: {
    show?: boolean;
    position?: 'top' | 'bottom' | 'left' | 'right';
  };
  /**
   * Custom renderer for the chart visualization
   */
  renderChart: (containerRef: React.RefObject<HTMLDivElement>, data: any[], theme: any) => React.ReactNode;
  /**
   * Loading state
   */
  isLoading?: boolean;
  /**
   * Error state
   */
  error?: Error | null;
  /**
   * Additional CSS class names
   */
  className?: string;
  /**
   * Chart container accessibility label
   */
  ariaLabel?: string;
  /**
   * Custom actions or controls
   */
  actions?: React.ReactNode;
}

/**
 * Base Chart component used to display various chart types
 * This is a container component that handles common features like titles,
 * loading states, error handling, and accessibility
 */
export const Chart: React.FC<ChartProps> = ({
  title,
  description,
  data,
  dimensions = { width: '100%', height: '300px' },
  legend = { show: true, position: 'bottom' },
  renderChart,
  isLoading = false,
  error = null,
  className,
  ariaLabel = 'Data visualization chart',
  actions,
}) => {
  const theme = useTheme();
  const chartContainerRef = React.useRef<HTMLDivElement>(null);
  
  // Handle loading and error states
  const renderContent = () => {
    if (isLoading) {
      return (
        <Flex 
          height="100%" 
          alignItems="center" 
          justifyContent="center"
          color="gray.500"
        >
          <Text>Loading chart data...</Text>
        </Flex>
      );
    }
    
    if (error) {
      return (
        <Flex 
          height="100%" 
          alignItems="center" 
          justifyContent="center"
          flexDirection="column"
          color="red.500"
          p={4}
        >
          <Text fontWeight="bold" mb={2}>Error loading chart</Text>
          <Text fontSize="sm">{error.message}</Text>
        </Flex>
      );
    }
    
    if (!data || data.length === 0) {
      return (
        <Flex 
          height="100%" 
          alignItems="center" 
          justifyContent="center"
          color="gray.500"
        >
          <Text>No data available</Text>
        </Flex>
      );
    }
    
    return renderChart(chartContainerRef, data, theme);
  };
  
  return (
    <Box 
      className={className} 
      borderRadius="md" 
      boxShadow="sm" 
      bg="white" 
      overflow="hidden"
      aria-label={ariaLabel}
      role="figure"
    >
      {/* Chart header with title and actions */}
      {(title || actions) && (
        <Box p={4} borderBottomWidth={1} borderBottomColor="gray.100">
          <Flex justifyContent="space-between" alignItems="center">
            <Box>
              {title && (
                <Text fontSize="md" fontWeight="bold" color="gray.700">
                  {title}
                </Text>
              )}
              {description && (
                <Text fontSize="sm" color="gray.500" mt={1}>
                  {description}
                </Text>
              )}
            </Box>
            {actions && (
              <Box>
                {actions}
              </Box>
            )}
          </Flex>
        </Box>
      )}
      
      {/* Chart visualization area */}
      <Box 
        ref={chartContainerRef} 
        width={dimensions.width} 
        height={dimensions.height}
        p={4}
      >
        {renderContent()}
      </Box>
      
      {/* Legend */}
      {legend.show && data && data.length > 0 && !isLoading && !error && (
        <Box 
          p={4} 
          borderTopWidth={1} 
          borderTopColor="gray.100"
        >
          <ChartLegend 
            data={data} 
            position={legend.position}
          />
        </Box>
      )}
    </Box>
  );
};

/**
 * Chart legend component to display data series information
 */
export const ChartLegend: React.FC<{
  data: any[];
  position?: 'top' | 'bottom' | 'left' | 'right';
}> = ({ 
  data,
  position = 'bottom'
}) => {
  // This is a simplified implementation
  // In a real application, you would generate the legend based on the data format
  const isVertical = position === 'left' || position === 'right';
  
  // Mock legend items for demonstration
  const legendItems = [
    { label: 'Series A', color: 'blue.500' },
    { label: 'Series B', color: 'green.500' },
    { label: 'Series C', color: 'purple.500' },
  ];
  
  const LegendContainer = isVertical ? VStack : HStack;
  
  return (
    <LegendContainer 
      spacing={4} 
      divider={isVertical ? <Divider /> : undefined}
      justify="center"
      width="100%"
    >
      {legendItems.map((item, index) => (
        <HStack key={index} spacing={2}>
          <Box 
            width="12px" 
            height="12px" 
            borderRadius="sm" 
            bg={item.color} 
          />
          <Text fontSize="sm">{item.label}</Text>
        </HStack>
      ))}
    </LegendContainer>
  );
};

export default Chart; 