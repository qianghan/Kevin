/**
 * Error Boundary Component
 * 
 * Catches JavaScript errors in child component tree and displays fallback UI.
 * Follows Single Responsibility Principle by focusing only on error handling.
 */

import React, { Component, ReactNode, ErrorInfo } from 'react';
import { Box, Heading, Text, Button, Flex, Icon } from '@chakra-ui/react';
import { useErrorService } from '../../services/service-context';

// Error boundary must be a class component
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetKeys?: any[];
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary class component
 */
class ErrorBoundaryClass extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render shows the fallback UI
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log the error to the error service
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    // If resetKeys change, reset the error boundary
    if (
      this.state.hasError &&
      this.props.resetKeys &&
      prevProps.resetKeys &&
      this.props.resetKeys.some((key, index) => key !== prevProps.resetKeys?.[index])
    ) {
      this.reset();
    }
  }

  reset = (): void => {
    this.setState({
      hasError: false,
      error: null
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Render custom fallback UI or default error UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Box
          p={5}
          borderRadius="md"
          borderWidth="1px"
          borderColor="red.300"
          bg="red.50"
          color="red.800"
          _dark={{
            bg: 'red.900',
            borderColor: 'red.700',
            color: 'white'
          }}
        >
          <Heading as="h3" size="md" mb={2}>
            Something went wrong
          </Heading>
          <Text mb={4}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </Text>
          <Button
            colorScheme="red"
            size="sm"
            onClick={this.reset}
          >
            Try again
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}

/**
 * Error boundary wrapper to connect with error service
 */
export const ErrorBoundary: React.FC<Omit<ErrorBoundaryProps, 'onError'>> = (props) => {
  // Get error service from context
  try {
    const errorService = useErrorService();
    
    const handleError = (error: Error, errorInfo: ErrorInfo) => {
      errorService.handleError(error, 'unknown', {
        component: 'ErrorBoundary',
        additionalData: {
          componentStack: errorInfo.componentStack
        }
      });
    };
    
    return <ErrorBoundaryClass {...props} onError={handleError} />;
  } catch (e) {
    // If service context is not available, fall back to basic error boundary
    return <ErrorBoundaryClass {...props} />;
  }
};

/**
 * Specialized error boundary variants
 */

interface FallbackProps {
  error: Error | null;
  resetErrorBoundary: () => void;
}

const DefaultFallback: React.FC<FallbackProps> = ({ error, resetErrorBoundary }) => (
  <Box
    p={5}
    borderRadius="md"
    borderWidth="1px"
    borderColor="red.300"
    bg="red.50"
    color="red.800"
    _dark={{
      bg: 'red.900',
      borderColor: 'red.700',
      color: 'white'
    }}
  >
    <Heading as="h3" size="md" mb={2}>
      Something went wrong
    </Heading>
    <Text mb={4}>
      {error?.message || 'An unexpected error occurred'}
    </Text>
    <Button
      colorScheme="red"
      size="sm"
      onClick={resetErrorBoundary}
    >
      Try again
    </Button>
  </Box>
);

/**
 * Creates an error boundary with a custom fallback component
 */
export function withErrorBoundary<P>(
  Component: React.ComponentType<P>,
  FallbackComponent: React.ComponentType<FallbackProps> = DefaultFallback
): React.ComponentType<P & { resetKeys?: any[] }> {
  const WithErrorBoundary = (props: P & { resetKeys?: any[] }) => {
    const { resetKeys, ...componentProps } = props;
    
    return (
      <ErrorBoundaryClass
        resetKeys={resetKeys}
        fallback={
          ({
            hasError,
            error,
            reset
          }: ErrorBoundaryState & { reset: () => void }) =>
            hasError ? (
              <FallbackComponent
                error={error}
                resetErrorBoundary={reset}
              />
            ) : null
        }
      >
        <Component {...componentProps as P} />
      </ErrorBoundaryClass>
    );
  };
  
  WithErrorBoundary.displayName = `withErrorBoundary(${
    Component.displayName || Component.name || 'Component'
  })`;
  
  return WithErrorBoundary;
}

/**
 * Card-style error fallback
 */
export const CardErrorFallback: React.FC<FallbackProps> = ({ error, resetErrorBoundary }) => (
  <Flex
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    p={6}
    borderRadius="md"
    borderWidth="1px"
    borderColor="red.300"
    bg="white"
    boxShadow="md"
    _dark={{
      bg: 'gray.800',
      borderColor: 'red.700',
    }}
  >
    <Icon
      viewBox="0 0 24 24"
      boxSize={12}
      color="red.500"
      mb={4}
    >
      <path
        fill="currentColor"
        d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 11c-.55 0-1-.45-1-1V8c0-.55.45-1 1-1s1 .45 1 1v4c0 .55-.45 1-1 1zm1 4h-2v-2h2v2z"
      />
    </Icon>
    
    <Heading as="h3" size="md" mb={2} textAlign="center">
      Something went wrong
    </Heading>
    
    <Text mb={4} textAlign="center">
      {error?.message || 'An unexpected error occurred'}
    </Text>
    
    <Button
      colorScheme="red"
      onClick={resetErrorBoundary}
    >
      Try again
    </Button>
  </Flex>
); 