import React from 'react';
import { Box, Flex, Text, Button, HStack, Circle, Divider, useBreakpointValue } from '@chakra-ui/react';

export interface Step {
  /**
   * Unique identifier for the step
   */
  id: string;
  /**
   * Step title
   */
  title: string;
  /**
   * Optional step description
   */
  description?: string;
  /**
   * Whether the step is optional
   */
  isOptional?: boolean;
  /**
   * Whether the step has been completed
   */
  isCompleted?: boolean;
  /**
   * Whether the step has encountered an error
   */
  hasError?: boolean;
  /**
   * Custom icon to display
   */
  icon?: React.ReactNode;
  /**
   * Content to render when this step is active
   */
  content?: React.ReactNode;
}

export interface StepperProps {
  /**
   * Array of step configurations
   */
  steps: Step[];
  /**
   * ID of the current active step
   */
  currentStepId: string;
  /**
   * Handler for step changes
   */
  onStepChange?: (stepId: string) => void;
  /**
   * Whether steps are clickable
   */
  isLinear?: boolean;
  /**
   * Orientation of the stepper
   */
  orientation?: 'horizontal' | 'vertical';
  /**
   * Custom renderer for step labels
   */
  renderStepLabel?: (step: Step, isActive: boolean, index: number) => React.ReactNode;
  /**
   * Handler for the next button
   */
  onNext?: () => void;
  /**
   * Handler for the back button
   */
  onBack?: () => void;
  /**
   * Custom text for the next button
   */
  nextButtonText?: string;
  /**
   * Custom text for the back button
   */
  backButtonText?: string;
  /**
   * Whether to show step numbers
   */
  showStepNumbers?: boolean;
  /**
   * Additional CSS class
   */
  className?: string;
}

/**
 * Stepper component for multi-step workflows
 */
export const Stepper: React.FC<StepperProps> = ({
  steps,
  currentStepId,
  onStepChange,
  isLinear = true,
  orientation = 'horizontal',
  renderStepLabel,
  onNext,
  onBack,
  nextButtonText = 'Next',
  backButtonText = 'Back',
  showStepNumbers = true,
  className,
}) => {
  // Responsive stepper layout
  const isVertical = orientation === 'vertical';
  const isMobile = useBreakpointValue({ base: true, md: false });
  const displayOrientation = isMobile ? 'vertical' : orientation;
  
  // Find current step index
  const currentStepIndex = steps.findIndex(step => step.id === currentStepId);
  const currentStep = steps[currentStepIndex];
  
  // Calculate progress percentage
  const progress = ((currentStepIndex) / (steps.length - 1)) * 100;
  
  // Handle step click
  const handleStepClick = (stepId: string, stepIndex: number) => {
    if (!onStepChange) return;
    
    // In linear mode, only allow navigating to completed steps or the next step
    if (isLinear) {
      const targetIndex = steps.findIndex(step => step.id === stepId);
      const canNavigate = targetIndex <= currentStepIndex + 1 && 
        steps.slice(0, targetIndex).every(step => step.isCompleted !== false);
      
      if (canNavigate) {
        onStepChange(stepId);
      }
    } else {
      // In non-linear mode, allow navigating to any step
      onStepChange(stepId);
    }
  };
  
  // Handle next/back navigation
  const handleNext = () => {
    if (currentStepIndex < steps.length - 1) {
      onStepChange?.(steps[currentStepIndex + 1].id);
      onNext?.();
    }
  };
  
  const handleBack = () => {
    if (currentStepIndex > 0) {
      onStepChange?.(steps[currentStepIndex - 1].id);
      onBack?.();
    }
  };
  
  // Render step indicator (number or icon)
  const renderStepIndicator = (step: Step, index: number, isActive: boolean) => {
    // Step status determines styling
    const isCompleted = step.isCompleted ?? (index < currentStepIndex);
    const isError = step.hasError ?? false;
    
    let bgColor = 'gray.200';
    let color = 'gray.600';
    let borderColor = 'transparent';
    
    if (isActive) {
      bgColor = 'blue.500';
      color = 'white';
      borderColor = 'blue.500';
    } else if (isCompleted) {
      bgColor = 'green.500';
      color = 'white';
    } else if (isError) {
      bgColor = 'red.500';
      color = 'white';
    }
    
    return (
      <Circle 
        size="32px" 
        bg={bgColor} 
        color={color}
        borderWidth={2}
        borderColor={borderColor}
        fontSize="sm"
        fontWeight="bold"
      >
        {isCompleted && !isError ? '✓' : (isError ? '!' : (showStepNumbers ? index + 1 : ''))}
      </Circle>
    );
  };
  
  return (
    <Box className={className} width="100%">
      {/* Stepper Header */}
      <Flex 
        direction={displayOrientation === 'vertical' ? 'column' : 'row'} 
        mb={8}
        width="100%"
      >
        {steps.map((step, index) => {
          const isActive = step.id === currentStepId;
          const isLast = index === steps.length - 1;
          
          return (
            <React.Fragment key={step.id}>
              {/* Step with indicator and label */}
              <Flex 
                direction={displayOrientation === 'vertical' ? 'row' : 'column'} 
                alignItems="center"
                flex={displayOrientation === 'vertical' ? undefined : 1}
                mb={displayOrientation === 'vertical' ? 4 : 0}
                cursor={onStepChange ? 'pointer' : 'default'}
                onClick={() => handleStepClick(step.id, index)}
                opacity={isActive || step.isCompleted ? 1 : 0.6}
                role="group"
                position="relative"
                aria-current={isActive ? 'step' : undefined}
              >
                {/* Step indicator */}
                {renderStepIndicator(step, index, isActive)}
                
                {/* Step label */}
                <Box
                  ml={displayOrientation === 'vertical' ? 4 : 0}
                  mt={displayOrientation === 'vertical' ? 0 : 2}
                  textAlign={displayOrientation === 'vertical' ? 'left' : 'center'}
                >
                  {renderStepLabel ? (
                    renderStepLabel(step, isActive, index)
                  ) : (
                    <>
                      <Text 
                        fontWeight={isActive ? 'bold' : 'medium'} 
                        color={isActive ? 'blue.700' : 'gray.700'}
                        _groupHover={{ color: 'blue.600' }}
                      >
                        {step.title}
                      </Text>
                      {step.description && (
                        <Text 
                          fontSize="sm" 
                          color="gray.500"
                          display={isMobile ? 'none' : 'block'}
                        >
                          {step.description}
                        </Text>
                      )}
                      {step.isOptional && (
                        <Text 
                          fontSize="xs" 
                          color="gray.400"
                          mt={1}
                          display={isMobile ? 'none' : 'block'}
                        >
                          Optional
                        </Text>
                      )}
                    </>
                  )}
                </Box>
              </Flex>
              
              {/* Connector line between steps */}
              {!isLast && (
                displayOrientation === 'vertical' ? (
                  <Box 
                    width="2px" 
                    height="24px" 
                    bg="gray.200" 
                    ml="16px" 
                    mb={2}
                  />
                ) : (
                  <Divider 
                    flex={1} 
                    alignSelf="center" 
                    borderColor="gray.200"
                    borderWidth="2px"
                    opacity={0.6}
                    display={{ base: 'none', md: 'block' }}
                  />
                )
              )}
            </React.Fragment>
          );
        })}
      </Flex>
      
      {/* Step Content */}
      <Box mb={8}>
        {currentStep?.content}
      </Box>
      
      {/* Navigation Buttons */}
      <Flex justifyContent="space-between" mt={6}>
        <Button 
          variant="outline" 
          onClick={handleBack} 
          isDisabled={currentStepIndex === 0}
        >
          {backButtonText}
        </Button>
        
        <Button 
          variant="solid" 
          colorScheme="blue" 
          onClick={handleNext} 
          isDisabled={currentStepIndex === steps.length - 1}
        >
          {nextButtonText}
        </Button>
      </Flex>
    </Box>
  );
};

/**
 * StepperContent component to render the active step content
 */
export const StepperContent: React.FC<{
  stepId: string;
  activeStepId: string;
  children: React.ReactNode;
}> = ({ stepId, activeStepId, children }) => {
  const isActive = stepId === activeStepId;
  
  if (!isActive) return null;
  
  return (
    <Box>
      {children}
    </Box>
  );
};

export default Stepper; 