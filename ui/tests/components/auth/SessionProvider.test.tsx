import React from 'react';
import { render, screen } from '@testing-library/react';
import { SessionProvider } from '../../../components/auth/SessionProvider';

// Mock the next-auth module
jest.mock('next-auth/react', () => {
  const originalModule = jest.requireActual('next-auth/react');
  return {
    ...originalModule,
    SessionProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="mock-session-provider">{children}</div>,
  };
});

describe('SessionProvider', () => {
  it('renders children correctly', () => {
    render(
      <SessionProvider>
        <div data-testid="test-child">Test Child</div>
      </SessionProvider>
    );

    const childElement = screen.getByTestId('test-child');
    expect(childElement).toBeInTheDocument();
    expect(childElement).toHaveTextContent('Test Child');
  });

  it('is wrapped with the NextAuth SessionProvider', () => {
    render(
      <SessionProvider>
        <div>Child Content</div>
      </SessionProvider>
    );

    const mockProvider = screen.getByTestId('mock-session-provider');
    expect(mockProvider).toBeInTheDocument();
  });
}); 