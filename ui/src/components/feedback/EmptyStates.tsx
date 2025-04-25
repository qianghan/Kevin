import React from 'react';
import { Box, Flex, Text, Button, Image, VStack } from '@chakra-ui/react';

export interface EmptyStateProps {
  /**
   * Type of empty state to display
   */
  type?: 'default' | 'search' | 'filter' | 'data' | 'error';
  /**
   * Main heading text
   */
  title: string;
  /**
   * Descriptive text explaining the empty state
   */
  message?: string;
  /**
   * Image or illustration to display
   */
  image?: string;
  /**
   * Alt text for the image
   */
  imageAlt?: string;
  /**
   * Primary action button text
   */
  actionText?: string;
  /**
   * Primary action button handler
   */
  onAction?: () => void;
  /**
   * Secondary action button text
   */
  secondaryActionText?: string;
  /**
   * Secondary action button handler
   */
  onSecondaryAction?: () => void;
  /**
   * Additional CSS classes
   */
  className?: string;
  /**
   * Custom icon to override the default
   */
  icon?: React.ReactNode;
}

/**
 * EmptyState component for displaying empty state feedback to users.
 * Provides contextual empty states with actionable elements.
 */
export const EmptyState: React.FC<EmptyStateProps> = ({
  type = 'default',
  title,
  message,
  image,
  imageAlt = 'Empty state illustration',
  actionText,
  onAction,
  secondaryActionText,
  onSecondaryAction,
  className,
  icon,
}) => {
  // Default content based on type
  const getDefaultContent = () => {
    switch (type) {
      case 'search':
        return {
          title: title || 'No results found',
          message: message || 'Try adjusting your search terms or filters to find what you\'re looking for.',
          icon: icon || '🔍',
        };
      case 'filter':
        return {
          title: title || 'No matching items',
          message: message || 'Try changing or clearing your filters to see more results.',
          icon: icon || '🔎',
        };
      case 'data':
        return {
          title: title || 'No data available',
          message: message || 'There is no data to display at this time.',
          icon: icon || '📊',
        };
      case 'error':
        return {
          title: title || 'Something went wrong',
          message: message || 'We encountered an error while loading this content.',
          icon: icon || '⚠️',
        };
      default:
        return {
          title: title || 'Nothing here yet',
          message: message || 'Get started by creating your first item.',
          icon: icon || '➕',
        };
    }
  };

  const content = getDefaultContent();

  return (
    <Flex 
      direction="column" 
      alignItems="center" 
      justifyContent="center" 
      textAlign="center"
      p={{ base: 4, md: 8 }}
      className={className}
      data-testid={`empty-state-${type}`}
      aria-live="polite"
      minH="240px"
    >
      {image ? (
        <Box mb={6} maxW="240px">
          <Image src={image} alt={imageAlt} />
        </Box>
      ) : (
        <Box mb={6} fontSize="4xl">
          {content.icon}
        </Box>
      )}

      <VStack spacing={2} mb={6}>
        <Text 
          fontSize="xl" 
          fontWeight="bold"
          color="text.primary"
        >
          {content.title}
        </Text>
        {content.message && (
          <Text 
            fontSize="md" 
            color="text.secondary"
            maxW="400px"
          >
            {content.message}
          </Text>
        )}
      </VStack>

      {(actionText || secondaryActionText) && (
        <Flex 
          gap={4} 
          flexDirection={{ base: 'column', sm: 'row' }}
          alignItems="center"
        >
          {actionText && (
            <Button 
              variant="primary" 
              onClick={onAction}
              data-testid="empty-state-primary-action"
            >
              {actionText}
            </Button>
          )}
          {secondaryActionText && (
            <Button 
              variant="outline" 
              onClick={onSecondaryAction}
              data-testid="empty-state-secondary-action"
            >
              {secondaryActionText}
            </Button>
          )}
        </Flex>
      )}
    </Flex>
  );
};

/**
 * Custom empty state for lists with no items
 */
export const EmptyList: React.FC<Omit<EmptyStateProps, 'type'>> = (props) => (
  <EmptyState 
    type="default" 
    title="No items yet" 
    message="Create your first item to get started."
    actionText="Create Item"
    {...props} 
  />
);

/**
 * Custom empty state for search results
 */
export const EmptySearch: React.FC<Omit<EmptyStateProps, 'type'>> = (props) => (
  <EmptyState 
    type="search" 
    {...props} 
  />
);

/**
 * Custom empty state for filtered results
 */
export const EmptyFilter: React.FC<Omit<EmptyStateProps, 'type'>> = (props) => (
  <EmptyState 
    type="filter" 
    {...props} 
  />
);

/**
 * Custom empty state for data visualizations
 */
export const EmptyData: React.FC<Omit<EmptyStateProps, 'type'>> = (props) => (
  <EmptyState 
    type="data" 
    {...props} 
  />
);

export default EmptyState; 