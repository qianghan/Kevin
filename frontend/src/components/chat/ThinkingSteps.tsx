/**
 * ThinkingSteps Component
 * 
 * This component visualizes the thinking steps of the AI model
 * in a collapsible, formatted display.
 */

import React from 'react';
import { 
  Box, 
  VStack, 
  Text, 
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Spinner,
  useColorModeValue
} from '@chakra-ui/react';
import { ThinkingStepsProps } from '../../interfaces/components/chat.components';

/**
 * ThinkingSteps Component
 * 
 * @param props - The component props
 * @returns A component displaying AI thinking steps
 */
export const ThinkingSteps: React.FC<ThinkingStepsProps> = ({
  steps = [],
  isLoading = false,
  isExpanded = false,
  onToggleExpand,
  testId = 'thinking-steps',
  ...boxProps
}) => {
  // Theme colors
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.700', 'gray.300');
  const headingColor = useColorModeValue('gray.600', 'gray.400');
  
  if (isLoading) {
    return (
      <Box 
        data-testid={`${testId}-loading`}
        p={4} 
        textAlign="center"
        {...boxProps}
      >
        <Spinner size="sm" mr={2} />
        <Text fontSize="sm">Loading thinking steps...</Text>
      </Box>
    );
  }
  
  if (steps.length === 0) {
    return (
      <Box 
        data-testid={`${testId}-empty`}
        p={4} 
        textAlign="center"
        {...boxProps}
      >
        <Text fontSize="sm" color={textColor}>No thinking steps available</Text>
      </Box>
    );
  }
  
  return (
    <Box
      data-testid={testId}
      bg={bgColor}
      borderWidth="1px"
      borderColor={borderColor}
      borderRadius="md"
      overflow="hidden"
      {...boxProps}
    >
      <Accordion defaultIndex={isExpanded ? [0] : []} allowMultiple>
        {steps.map((step, index) => (
          <AccordionItem key={`step-${index}`} border="0">
            <AccordionButton py={2}>
              <Box flex="1" textAlign="left">
                <Text fontWeight="medium" fontSize="sm" color={headingColor}>
                  Step {index + 1}: {step.title || 'Thinking'}
                </Text>
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4}>
              <Box
                p={3}
                bg={useColorModeValue('white', 'gray.900')}
                borderRadius="md"
                fontSize="sm"
                fontFamily="mono"
                whiteSpace="pre-wrap"
                overflowX="auto"
              >
                {step.content}
              </Box>
            </AccordionPanel>
          </AccordionItem>
        ))}
      </Accordion>
    </Box>
  );
};

export default ThinkingSteps; 