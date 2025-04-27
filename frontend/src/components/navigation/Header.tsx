import React, { ReactNode } from 'react';
import { 
  Box, 
  Heading, 
  Text, 
  Flex,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink
} from '@chakra-ui/react';

// Interface for breadcrumb items (ISP)
export interface BreadcrumbItemProps {
  label: string;
  href?: string;
  isCurrentPage?: boolean;
}

// Interface for header props (ISP)
interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbItems?: BreadcrumbItemProps[];
  actions?: ReactNode;
}

// Page header component (SRP)
export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  breadcrumbItems,
  actions,
}) => {
  return (
    <Box mb={6}>
      {/* Breadcrumbs */}
      {breadcrumbItems && breadcrumbItems.length > 0 && (
        <Breadcrumb mb={3} fontSize="sm" opacity={0.7}>
          {breadcrumbItems.map((item, index) => (
            <BreadcrumbItem key={index} isCurrentPage={item.isCurrentPage}>
              {item.href && !item.isCurrentPage ? (
                <BreadcrumbLink href={item.href}>{item.label}</BreadcrumbLink>
              ) : (
                <Text>{item.label}</Text>
              )}
            </BreadcrumbItem>
          ))}
        </Breadcrumb>
      )}
      
      {/* Header content */}
      <Flex justifyContent="space-between" alignItems="flex-start">
        <Box>
          <Heading as="h1" size="xl">{title}</Heading>
          {subtitle && (
            <Text mt={1} fontSize="md" opacity={0.8}>
              {subtitle}
            </Text>
          )}
        </Box>
        
        {/* Optional action buttons */}
        {actions && (
          <Box ml={4}>
            {actions}
          </Box>
        )}
      </Flex>
    </Box>
  );
};

export default PageHeader; 