/**
 * Accessibility Utilities
 * 
 * Provides helper functions and utilities for improving accessibility.
 * Includes focus management, screen reader announcements, and ARIA attribute helpers.
 */

/**
 * Focus Management
 * 
 * Utilities for managing focus in the UI.
 */

/**
 * Traps focus within a specified element
 * @param element The element to trap focus within
 * @returns A cleanup function to remove the trap
 */
export function trapFocus(element: HTMLElement): () => void {
  if (!element) return () => {};

  // Find all focusable elements
  const focusableElements = element.querySelectorAll(
    'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
  );

  if (focusableElements.length === 0) return () => {};

  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

  // Set initial focus if nothing inside is focused
  if (!element.contains(document.activeElement)) {
    firstElement.focus();
  }

  // Handle keydown events
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    // Shift + Tab on first element
    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    }
    // Tab on last element
    else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  };

  // Add event listener
  element.addEventListener('keydown', handleKeyDown);

  // Return cleanup function
  return () => {
    element.removeEventListener('keydown', handleKeyDown);
  };
}

/**
 * Returns focus to a specific element
 * @param element Element to return focus to
 */
export function returnFocus(element: HTMLElement): void {
  if (element && typeof element.focus === 'function') {
    // Use setTimeout to ensure the focus happens after any other
    // operations that might affect focus
    setTimeout(() => {
      element.focus();
    }, 0);
  }
}

/**
 * Gets all focusable elements within a container
 * @param container Element to search within
 * @returns Array of focusable elements
 */
export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  if (!container) return [];

  const selector = 
    'a[href], button:not([disabled]), textarea:not([disabled]), ' +
    'input:not([disabled]), select:not([disabled]), ' +
    '[tabindex]:not([tabindex="-1"])';

  return Array.from(container.querySelectorAll(selector));
}

/**
 * Manages focus within a container when elements are added or removed
 * @param container Element to monitor
 * @param options Configuration options
 * @returns Cleanup function
 */
export function manageFocus(
  container: HTMLElement,
  options: {
    autoFocus?: boolean;
    focusFirst?: boolean;
    onFocusEscape?: () => void;
  } = {}
): () => void {
  if (!container) return () => {};

  const { autoFocus = true, focusFirst = false, onFocusEscape } = options;
  
  // Store previously focused element
  const previouslyFocused = document.activeElement as HTMLElement;

  // Focus first element or container if focusFirst is true
  if (autoFocus) {
    if (focusFirst) {
      const focusableElements = getFocusableElements(container);
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      } else {
        container.focus();
      }
    } else {
      container.focus();
    }
  }

  // Handle focus leaving the container
  const handleFocusIn = (e: FocusEvent) => {
    if (container && !container.contains(e.target as Node) && onFocusEscape) {
      onFocusEscape();
    }
  };

  // Add listener for focus events
  document.addEventListener('focusin', handleFocusIn);

  // Return cleanup function
  return () => {
    document.removeEventListener('focusin', handleFocusIn);
    
    // Return focus to previously focused element
    if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
      previouslyFocused.focus();
    }
  };
}

/**
 * Screen Reader Utilities
 * 
 * Functions for optimizing screen reader experiences.
 */

/**
 * Announces a message to screen reader users
 * @param message Message to announce
 * @param options Configuration options
 */
export function announceToScreenReader(
  message: string,
  options: {
    politeness?: 'polite' | 'assertive';
    clearAfter?: number;
  } = {}
): void {
  if (!message) return;

  const { politeness = 'polite', clearAfter = 5000 } = options;

  // Create or find the live region element
  let liveRegion = document.getElementById(
    politeness === 'assertive' ? 'a11y-assertive' : 'a11y-polite'
  );

  if (!liveRegion) {
    liveRegion = document.createElement('div');
    liveRegion.id = politeness === 'assertive' ? 'a11y-assertive' : 'a11y-polite';
    liveRegion.setAttribute('aria-live', politeness);
    liveRegion.setAttribute('role', 'log');
    liveRegion.setAttribute('aria-relevant', 'additions');
    liveRegion.style.position = 'absolute';
    liveRegion.style.width = '1px';
    liveRegion.style.height = '1px';
    liveRegion.style.margin = '-1px';
    liveRegion.style.padding = '0';
    liveRegion.style.overflow = 'hidden';
    liveRegion.style.clip = 'rect(0, 0, 0, 0)';
    liveRegion.style.border = '0';
    document.body.appendChild(liveRegion);
  }

  // Add the message
  liveRegion.textContent = '';
  
  // Using setTimeout to ensure the DOM change is registered
  setTimeout(() => {
    liveRegion!.textContent = message;
  }, 50);

  // Clear the message after specified time
  if (clearAfter > 0) {
    setTimeout(() => {
      if (liveRegion) {
        liveRegion.textContent = '';
      }
    }, clearAfter);
  }
}

/**
 * Provides a descriptive label for an element
 * @param element Element to label
 * @param label Text label
 */
export function provideLabelFor(element: HTMLElement, label: string): void {
  if (!element || !label) return;

  // Generate a unique ID for the element if it doesn't have one
  if (!element.id) {
    element.id = `a11y-el-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Create or find the label element
  let labelElement = document.getElementById(`label-${element.id}`);
  
  if (!labelElement) {
    labelElement = document.createElement('span');
    labelElement.id = `label-${element.id}`;
    labelElement.style.position = 'absolute';
    labelElement.style.width = '1px';
    labelElement.style.height = '1px';
    labelElement.style.margin = '-1px';
    labelElement.style.padding = '0';
    labelElement.style.overflow = 'hidden';
    labelElement.style.clip = 'rect(0, 0, 0, 0)';
    labelElement.style.border = '0';
    
    // Insert the label before the element
    element.parentNode?.insertBefore(labelElement, element);
  }

  // Set the label text
  labelElement.textContent = label;

  // Associate the label with the element
  element.setAttribute('aria-labelledby', labelElement.id);
}

/**
 * Describes an element for screen readers
 * @param element Element to describe
 * @param description Description text
 */
export function provideDescriptionFor(element: HTMLElement, description: string): void {
  if (!element || !description) return;

  // Generate a unique ID for the element if it doesn't have one
  if (!element.id) {
    element.id = `a11y-el-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Create or find the description element
  let descriptionElement = document.getElementById(`desc-${element.id}`);
  
  if (!descriptionElement) {
    descriptionElement = document.createElement('span');
    descriptionElement.id = `desc-${element.id}`;
    descriptionElement.style.position = 'absolute';
    descriptionElement.style.width = '1px';
    descriptionElement.style.height = '1px';
    descriptionElement.style.margin = '-1px';
    descriptionElement.style.padding = '0';
    descriptionElement.style.overflow = 'hidden';
    descriptionElement.style.clip = 'rect(0, 0, 0, 0)';
    descriptionElement.style.border = '0';
    
    // Insert the description after the element
    element.parentNode?.insertBefore(descriptionElement, element.nextSibling);
  }

  // Set the description text
  descriptionElement.textContent = description;

  // Associate the description with the element
  element.setAttribute('aria-describedby', descriptionElement.id);
}

/**
 * ARIA Attribute Helpers
 * 
 * Utilities for setting and managing ARIA attributes.
 */

/**
 * Sets element role
 * @param element Element to set role on
 * @param role ARIA role
 */
export function setRole(element: HTMLElement, role: string): void {
  if (!element || !role) return;
  element.setAttribute('role', role);
}

/**
 * Sets ARIA expanded attribute
 * @param element Element to set attribute on
 * @param expanded Expanded state
 */
export function setExpanded(element: HTMLElement, expanded: boolean): void {
  if (!element) return;
  element.setAttribute('aria-expanded', expanded.toString());
}

/**
 * Sets ARIA hidden attribute
 * @param element Element to set attribute on
 * @param hidden Hidden state
 */
export function setHidden(element: HTMLElement, hidden: boolean): void {
  if (!element) return;
  element.setAttribute('aria-hidden', hidden.toString());
}

/**
 * Sets ARIA selected attribute
 * @param element Element to set attribute on
 * @param selected Selected state
 */
export function setSelected(element: HTMLElement, selected: boolean): void {
  if (!element) return;
  element.setAttribute('aria-selected', selected.toString());
}

/**
 * Sets ARIA checked attribute
 * @param element Element to set attribute on
 * @param checked Checked state
 */
export function setChecked(element: HTMLElement, checked: boolean): void {
  if (!element) return;
  element.setAttribute('aria-checked', checked.toString());
}

/**
 * Sets ARIA pressed attribute
 * @param element Element to set attribute on
 * @param pressed Pressed state
 */
export function setPressed(element: HTMLElement, pressed: boolean): void {
  if (!element) return;
  element.setAttribute('aria-pressed', pressed.toString());
}

/**
 * Accessibility Detection
 * 
 * Utilities for detecting accessibility settings and preferences.
 */

/**
 * Detects if the user prefers reduced motion
 * @returns True if the user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Detects if the user has a screen reader active (approximate detection)
 * Note: This is not 100% reliable
 * @returns Promise resolving to true if a screen reader is likely active
 */
export async function detectScreenReader(): Promise<boolean> {
  // No reliable way to detect screen readers
  // This is a best-effort approach based on common patterns
  return new Promise(resolve => {
    // Check for common screen reader classes that might be added to the body
    const bodyClasses = document.body.className.toLowerCase();
    if (
      bodyClasses.includes('sr-active') || 
      bodyClasses.includes('screenreader') ||
      bodyClasses.includes('nvda') ||
      bodyClasses.includes('jaws') ||
      bodyClasses.includes('voiceover')
    ) {
      resolve(true);
      return;
    }

    // Listen for keyboard navigation which is common with screen readers
    let tabCount = 0;
    const keyHandler = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        tabCount++;
        if (tabCount >= 3) {
          document.removeEventListener('keydown', keyHandler);
          resolve(true);
        }
      }
    };

    // Set a timeout to resolve to false if no other indicators
    setTimeout(() => {
      document.removeEventListener('keydown', keyHandler);
      resolve(false);
    }, 3000);

    document.addEventListener('keydown', keyHandler);
  });
}

/**
 * Detects if high contrast mode is active
 * @returns True if high contrast mode is likely active
 */
export function isHighContrastMode(): boolean {
  // Create a test element
  const testElement = document.createElement('div');
  testElement.style.position = 'absolute';
  testElement.style.width = '1px';
  testElement.style.height = '1px';
  testElement.style.backgroundColor = 'transparent';
  testElement.style.backgroundImage = 'url("data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")';
  testElement.style.border = '0';
  testElement.style.padding = '0';
  
  document.body.appendChild(testElement);
  
  // Check computed style
  const computedStyle = window.getComputedStyle(testElement);
  const hasBackgroundImage = computedStyle.backgroundImage !== 'none';
  
  document.body.removeChild(testElement);
  
  // In high contrast mode, background images are often removed
  return !hasBackgroundImage;
} 