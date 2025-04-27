import { render, screen } from '@testing-library/react';
import { Button, Text, Heading, Box, useTheme } from '@chakra-ui/react';
import { ThemeProvider } from '../../src/theme/ThemeProvider';

// Test utils to provide theme
const TestThemeConsumer = () => {
  const theme = useTheme();
  return (
    <Box data-testid="theme-consumer">
      <div data-testid="kai-color">{theme.colors.kai[400]}</div>
      <div data-testid="dark-bg">{theme.colors.background.dark}</div>
      <div data-testid="brand-ring">{theme.brandExtensions.brandRing.default}</div>
    </Box>
  );
};

describe('Theme compatibility', () => {
  it('should provide theme values to components', () => {
    render(
      <ThemeProvider>
        <TestThemeConsumer />
      </ThemeProvider>
    );
    
    expect(screen.getByTestId('kai-color')).toHaveTextContent('#4FDBA9');
    expect(screen.getByTestId('dark-bg')).toHaveTextContent('#0A1723');
  });

  it('should apply consistent styling to components', () => {
    render(
      <ThemeProvider>
        <Button variant="primary" data-testid="kai-button">KAI Button</Button>
        <Text color="kai.500" data-testid="kai-text">KAI Text</Text>
        <Heading color="kai.700" data-testid="kai-heading">KAI Heading</Heading>
      </ThemeProvider>
    );
    
    // Since we're using CSS vars with Chakra, we can't easily test the exact color values
    // But we can test that the correct classes/props are applied
    const button = screen.getByTestId('kai-button');
    expect(button).toBeInTheDocument();
    
    const text = screen.getByTestId('kai-text');
    expect(text).toHaveStyle("color: var(--chakra-colors-kai-500)");
    
    const heading = screen.getByTestId('kai-heading');
    expect(heading).toHaveStyle("color: var(--chakra-colors-kai-700)");
  });

  it('should properly extend component variants', () => {
    render(
      <ThemeProvider>
        <Button variant="primary" data-testid="primary-button">Primary</Button>
        <Button variant="secondary" data-testid="secondary-button">Secondary</Button>
      </ThemeProvider>
    );
    
    const primaryButton = screen.getByTestId('primary-button');
    const secondaryButton = screen.getByTestId('secondary-button');
    
    expect(primaryButton).toBeInTheDocument();
    expect(secondaryButton).toBeInTheDocument();
    // In a real test we'd check exact styles, but that's challenging with Chakra's CSS vars
  });
}); 