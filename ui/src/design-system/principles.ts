/**
 * KAI Design Language and Principles
 * 
 * This file defines the core design principles, rules, and guidelines for the KAI UI Design System.
 * It serves as a central reference for maintaining consistency across the application.
 */

// ----------------------------------------------------------------------------
// Design Principles
// ----------------------------------------------------------------------------

/**
 * Core design principles that guide all KAI design decisions
 */
export const designPrinciples = {
  /**
   * Simplicity - KAI interfaces prioritize clarity and ease of use
   */
  simplicity: {
    description: 'Create interfaces that are intuitive and minimize cognitive load',
    guidelines: [
      'Avoid unnecessary UI elements and decorations',
      'Prioritize content over chrome',
      'Use progressive disclosure for complex tasks',
      'Minimize the number of actions required to complete a task'
    ]
  },

  /**
   * Consistency - KAI interfaces maintain visual and behavioral consistency
   */
  consistency: {
    description: 'Maintain consistent patterns across the application',
    guidelines: [
      'Use the same interaction patterns for similar actions',
      'Apply common visual treatments for similar components',
      'Ensure terminology is consistent across the interface',
      'Follow established platform conventions when appropriate'
    ]
  },

  /**
   * Responsive - KAI interfaces adapt gracefully to different devices and contexts
   */
  responsive: {
    description: 'Design for all devices and contexts',
    guidelines: [
      'Start with mobile layouts and enhance for larger screens',
      'Use relative units for measurements (rem, %, etc.)',
      'Test designs across breakpoints',
      'Ensure touch targets are appropriately sized'
    ]
  },

  /**
   * Accessible - KAI interfaces are usable by everyone
   */
  accessible: {
    description: 'Create interfaces that work for all users regardless of abilities',
    guidelines: [
      'Meet WCAG 2.1 AA standards at minimum',
      'Support keyboard navigation for all interactive elements',
      'Ensure sufficient color contrast',
      'Provide alternative text for images',
      'Design with screen readers in mind'
    ]
  },

  /**
   * Purposeful - KAI interfaces prioritize user goals and tasks
   */
  purposeful: {
    description: 'Every element has a clear purpose that serves user goals',
    guidelines: [
      'Design with specific user journeys in mind',
      'Question the necessity of each element',
      'Prioritize high-frequency tasks',
      'Use data and feedback to inform design decisions'
    ]
  }
};

// ----------------------------------------------------------------------------
// Grid System Rules
// ----------------------------------------------------------------------------

/**
 * Grid system definition and rules
 */
export const gridSystem = {
  /**
   * Base grid configuration
   */
  baseGrid: {
    columns: {
      mobile: 4,
      tablet: 8,
      desktop: 12,
      wide: 16
    },
    gutter: {
      mobile: '16px',
      tablet: '24px',
      desktop: '32px',
      wide: '40px'
    },
    margin: {
      mobile: '16px',
      tablet: '32px',
      desktop: '64px',
      wide: '80px'
    }
  },

  /**
   * Breakpoints for responsive design
   */
  breakpoints: {
    sm: '30em',    // 480px
    md: '48em',    // 768px
    lg: '62em',    // 992px
    xl: '80em',    // 1280px
    '2xl': '96em', // 1536px
  },

  /**
   * Grid layout usage guidelines
   */
  guidelines: [
    'Use the grid system for all layout decisions to maintain consistency',
    'Align components to the grid; avoid arbitrary positioning',
    'Allow components to span multiple columns when appropriate',
    'Maintain consistent spacing between grid items',
    'Consider the "safe area" on mobile devices when placing content',
    'Content should be centered within the grid at wide viewports'
  ]
};

// ----------------------------------------------------------------------------
// Component Hierarchy
// ----------------------------------------------------------------------------

/**
 * Component hierarchy and classification
 */
export const componentHierarchy = {
  /**
   * 1. Foundation - Base design tokens and utilities
   */
  foundation: {
    description: 'Core design tokens and utilities that form the foundation of the design system',
    components: [
      'Colors',
      'Typography',
      'Spacing',
      'Borders',
      'Shadows',
      'Z-Index',
      'Animations'
    ]
  },

  /**
   * 2. Elements - Atomic UI components 
   */
  elements: {
    description: 'Atomic components that are the building blocks of the interface',
    components: [
      'Button',
      'Input',
      'Checkbox',
      'Radio',
      'Toggle',
      'Icon',
      'Text',
      'Heading'
    ]
  },

  /**
   * 3. Components - Composed elements that form reusable UI components
   */
  components: {
    description: 'Composed components that combine multiple elements',
    components: [
      'Card',
      'Form',
      'Modal',
      'Alert',
      'Toast',
      'Table',
      'List',
      'Tabs',
      'Dropdown'
    ]
  },

  /**
   * 4. Patterns - Higher-order components that implement specific UX patterns
   */
  patterns: {
    description: 'Components that implement specific UX patterns',
    components: [
      'Navigation',
      'DataTable',
      'Pagination',
      'SearchBar',
      'FileUpload',
      'Wizard',
      'Dashboard'
    ]
  },

  /**
   * 5. Templates - Page-level layouts
   */
  templates: {
    description: 'Page-level layouts and templates',
    components: [
      'AppLayout',
      'AuthLayout',
      'MarketingLayout',
      'SettingsLayout',
      'DashboardLayout'
    ]
  }
};

// ----------------------------------------------------------------------------
// Composition Rules
// ----------------------------------------------------------------------------

/**
 * Rules for component composition and extension
 */
export const compositionRules = {
  /**
   * Nesting guidelines for organizing components
   */
  nesting: [
    'Limit nesting depth to avoid complexity',
    'Use composition over inheritance',
    'Keep components focused on a single responsibility',
    'Break complex UIs into smaller, reusable components'
  ],

  /**
   * Extension guidelines for customizing components
   */
  extension: [
    'Extend components through props, not by modification',
    'Use composition to combine functionality',
    'Create higher-order components for cross-cutting concerns',
    'Use theme customization for visual changes'
  ],

  /**
   * State management in component composition
   */
  stateManagement: [
    'Keep state as local as possible',
    'Lift state only when necessary',
    'Use context for theme, user preferences, and authentication',
    'Pass callbacks for state changes to child components'
  ],

  /**
   * Accessibility in component composition
   */
  accessibility: [
    'Ensure proper HTML semantics in component structure',
    'Maintain proper heading hierarchy',
    'Use ARIA attributes appropriately',
    'Ensure keyboard navigation works within composed components',
    'Test components with screenreaders'
  ]
};

// ----------------------------------------------------------------------------
// Usage Examples
// ----------------------------------------------------------------------------

/**
 * Example of proper component composition
 */
export const exampleComposition = `
// Example of proper component composition
import { Box, Card, Heading, Text, Button } from 'kai-ui';

const ProductCard = ({ product, onAddToCart }) => (
  <Card variant="outlined" p="md">
    <Box mb="md">
      <img src={product.image} alt={product.name} />
    </Box>
    <Heading size="md" mb="xs">{product.name}</Heading>
    <Text color="text.secondary" mb="md">{product.description}</Text>
    <Box display="flex" justifyContent="space-between" alignItems="center">
      <Text fontWeight="bold">${product.price}</Text>
      <Button 
        variant="primary" 
        onClick={() => onAddToCart(product)}
      >
        Add to Cart
      </Button>
    </Box>
  </Card>
);
`;

/**
 * Example of responsive design using the grid system
 */
export const exampleResponsiveGrid = `
// Example of responsive design with the grid system
import { ResponsiveGrid, Card } from 'kai-ui';

const ProductGrid = ({ products }) => (
  <ResponsiveGrid 
    columns={{ 
      base: 1,
      sm: 2,
      md: 3,
      lg: 4 
    }}
    spacing={{ 
      base: 'md',
      md: 'lg' 
    }}
  >
    {products.map(product => (
      <Card key={product.id} product={product} />
    ))}
  </ResponsiveGrid>
);
`;

export default {
  designPrinciples,
  gridSystem,
  componentHierarchy,
  compositionRules,
}; 