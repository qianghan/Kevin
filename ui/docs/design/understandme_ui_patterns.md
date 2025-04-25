# KAI UI Patterns Documentation

This document provides comprehensive information about UI patterns implemented in the KAI Design System. It includes guidelines for composition, accessibility, and responsive behavior for each pattern.

## Table of Contents

1. [Card Patterns](#card-patterns)
2. [Form Patterns](#form-patterns)
3. [Error State Patterns](#error-state-patterns)
4. [Loading State Patterns](#loading-state-patterns)
5. [Empty State Patterns](#empty-state-patterns)
6. [Notification Patterns](#notification-patterns)
7. [Data Visualization Patterns](#data-visualization-patterns)
8. [Multi-step Workflow Patterns](#multi-step-workflow-patterns)
9. [Grid and Layout Patterns](#grid-and-layout-patterns)
10. [Navigation Patterns](#navigation-patterns)
11. [Interaction Patterns](#interaction-patterns)

## Card Patterns

Cards are used to group related information and actions. They create discrete, contained units of content or functionality.

### Variants

- **Basic Card**: Simple container with padding and optional border/shadow
- **Interactive Card**: Clickable card with hover/active states
- **Expandable Card**: Card that can be expanded to show more content
- **Media Card**: Card containing image or video elements

### Composition Rules

```jsx
// Basic composition
<Card>
  <Card.Header>Card Title</Card.Header>
  <Card.Body>Card content goes here...</Card.Body>
  <Card.Footer>
    <Button>Action</Button>
  </Card.Footer>
</Card>

// Interactive card
<Card 
  variant="interactive" 
  onClick={handleCardClick}
>
  Card content...
</Card>

// Expandable card
<Card isExpandable initialExpanded={false}>
  <Card.Header>
    <CardTitle>Expandable Card</CardTitle>
    <ExpandToggle />
  </Card.Header>
  <Card.Body>
    <ExpandableContent>
      This content is expandable...
    </ExpandableContent>
  </Card.Body>
</Card>
```

### Accessibility Guidelines

- Use appropriate heading levels within cards for proper document structure
- Ensure interactive cards have proper focus states
- For interactive cards, use appropriate ARIA roles (e.g., `role="button"`)
- Expandable cards should use `aria-expanded` and `aria-controls` attributes

### Responsive Behavior

- On mobile, cards typically expand to full width (minus container padding)
- Content within cards should adapt to available space (e.g., text wrapping)
- Media cards should scale images appropriately or use different aspect ratios on different devices
- Interactive cards should have larger touch targets on mobile devices

## Form Patterns

Forms collect and validate user input. They should be intuitive, accessible, and provide clear feedback.

### Variants

- **Simple Form**: Basic form with standard inputs
- **Multi-step Form**: Form divided into logical sections or steps
- **Inline Form**: Compact form with horizontal layout
- **Search Form**: Specialized form for search functionality

### Composition Rules

```jsx
// Basic form structure
<Form onSubmit={handleSubmit}>
  <FormField 
    name="email" 
    label="Email Address"
    validate={validateEmail}
    isRequired
  />
  <FormField 
    name="password" 
    type="password" 
    label="Password"
    isRequired
  />
  <Button type="submit">Submit</Button>
</Form>

// Multi-step form
<Stepper steps={formSteps} currentStepId={currentStep}>
  <StepperContent stepId="personal-info">
    <FormField name="name" label="Full Name" />
    <FormField name="email" label="Email" />
  </StepperContent>
  <StepperContent stepId="account-details">
    <FormField name="username" label="Username" />
    <FormField name="password" type="password" label="Password" />
  </StepperContent>
</Stepper>
```

### Accessibility Guidelines

- All form controls must have associated labels
- Use fieldsets and legends to group related form controls
- Provide clear error messages that are associated with inputs using `aria-describedby`
- Required fields should be indicated visually and with `aria-required="true"`
- Ensure proper keyboard navigation order
- Support both mouse and keyboard interactions for all form controls

### Responsive Behavior

- Form layouts should adjust from multi-column to single-column on smaller viewports
- Input sizes should adapt to viewport width
- Consider breaking complex forms into steps on mobile
- Ensure touch targets are at least 44px × 44px on mobile
- Text inputs should be at least 16px to prevent zoom on iOS

## Error State Patterns

Error states communicate problems or failures to users and provide guidance on how to resolve them.

### Variants

- **Inline Error**: Displayed directly with form inputs
- **Toast Error**: Temporary notification for non-critical errors
- **Modal Error**: Blocking dialog for critical errors
- **Page Error**: Full-page error view for system failures

### Composition Rules

```jsx
// Inline error
<FormControl isInvalid={!!errors.email}>
  <FormLabel htmlFor="email">Email</FormLabel>
  <Input id="email" {...register('email')} />
  <FormErrorMessage>{errors.email?.message}</FormErrorMessage>
</FormControl>

// Toast error
useNotification().show({
  title: 'Connection Error',
  message: 'Unable to connect to server. Please try again.',
  status: 'error',
  duration: 5000,
});

// Page error
<ErrorState
  type="error"
  title="Something went wrong"
  message="We encountered an error while loading this page."
  actionText="Refresh Page"
  onAction={() => window.location.reload()}
/>
```

### Accessibility Guidelines

- Error messages should be clear, concise, and helpful
- Use appropriate colors (not only color) to indicate errors
- Ensure sufficient color contrast for error text
- Use `aria-invalid="true"` for invalid form fields
- Connect error messages to inputs using `aria-describedby`
- For toast notifications, use `role="alert"` and `aria-live="assertive"`

### Responsive Behavior

- Error messages should wrap properly on small screens
- Toast errors should be positioned appropriately on different devices
- Modal errors should be properly sized and positioned on all devices
- Page errors should be fully responsive with properly sized content

## Loading State Patterns

Loading states indicate that content is being processed or loaded, preventing user confusion during wait times.

### Variants

- **Spinner**: Simple animated icon for small elements
- **Progress Bar**: Linear indicator showing completion percentage
- **Skeleton Screen**: Content placeholder showing layout before content loads
- **Full-page Loader**: Overlay for page-level loading

### Composition Rules

```jsx
// Simple spinner
<Button isLoading loadingText="Submitting...">
  Submit
</Button>

// Skeleton screen
<Card>
  <Skeleton height="32px" width="50%" mb={4} />
  <Skeleton height="100px" mb={4} />
  <SkeletonText noOfLines={3} spacing={4} />
</Card>

// Progress loading
<Box>
  <Text mb={2}>Uploading file... {progress}%</Text>
  <Progress value={progress} max={100} />
</Box>
```

### Accessibility Guidelines

- Use `aria-busy="true"` on elements that are loading
- For progress indicators, use `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, and `aria-valuemax`
- Provide text alternatives for visual loading indicators
- Consider adding a time estimate for longer operations
- Ensure loading states have sufficient contrast

### Responsive Behavior

- Spinners and loaders should be appropriately sized for different viewports
- Skeleton screens should match the layout of the content they're replacing at various breakpoints
- Progress bars should scale with container width
- Full-page loaders should be positioned properly on all devices

## Empty State Patterns

Empty states guide users when there's no content to display, helping them understand the context and take appropriate actions.

### Variants

- **Default Empty**: For lists or collections with no items
- **Search Empty**: When search returns no results
- **Filter Empty**: When filters eliminate all results
- **Error Empty**: When content can't be loaded due to an error

### Composition Rules

```jsx
// Default empty state
<EmptyState
  title="No items yet"
  message="Create your first item to get started."
  actionText="Create Item"
  onAction={handleCreateItem}
/>

// Search empty state
<EmptySearch
  title="No results found"
  message="Try adjusting your search terms or filters."
  actionText="Clear Filters"
  onAction={clearFilters}
/>
```

### Accessibility Guidelines

- Ensure empty state illustrations have appropriate alt text
- Use semantic HTML to structure empty state content
- Make action buttons fully accessible with appropriate labels
- Use `aria-live="polite"` for dynamically changing empty states

### Responsive Behavior

- Illustrations should scale or be replaced with simpler versions on mobile
- Text should wrap and remain readable on all devices
- Action buttons should be properly sized for touch on mobile
- Consider simplified messaging on smaller screens

## Notification Patterns

Notifications inform users about system events, action results, or required attention.

### Variants

- **Toast**: Temporary, non-modal notification
- **Banner**: Persistent notification at the top of the page
- **Inline**: Contextual notification within content
- **Notification Center**: Collected history of notifications

### Composition Rules

```jsx
// Toast notification
useNotification().show({
  title: 'Success',
  message: 'Your profile has been updated.',
  status: 'success',
  duration: 3000,
});

// Banner notification
<Banner 
  status="warning"
  title="Your account will expire soon"
  message="Renew your subscription to maintain access."
  actionText="Renew Now"
  onAction={handleRenew}
  onClose={closeBanner}
/>

// Notification center
<NotificationCenter />
```

### Accessibility Guidelines

- Use appropriate ARIA roles: `role="alert"` for important notifications, `role="status"` for non-critical ones
- Use `aria-live="assertive"` for critical notifications, `aria-live="polite"` for others
- Ensure notifications can be dismissed by keyboard
- Provide sufficient time for users to read notifications before auto-dismissing
- Use both color and icons to communicate status (not just color)

### Responsive Behavior

- Toasts should be positioned appropriately on different devices (typically top-center on mobile)
- Banners should adapt to screen width with text wrapping as needed
- Notification center should switch to a full-screen or slide-in panel on mobile
- Ensure touch targets for actions and dismiss buttons are sufficient size

## Data Visualization Patterns

Data visualizations present complex information in graphical form, making it easier to understand and analyze.

### Variants

- **Charts**: Line, bar, pie, and other standard chart types
- **Dashboards**: Collections of related data visualizations
- **Data Tables**: Tabular data with sorting and filtering
- **Data Cards**: Key metrics displayed in card format

### Composition Rules

```jsx
// Basic chart
<Chart 
  title="Monthly Revenue"
  description="Revenue trends over the past 12 months"
  data={revenueData}
  renderChart={(ref, data, theme) => (
    // Render chart implementation with chart library
  )}
  dimensions={{ height: '400px' }}
/>

// Data card
<DataCard
  title="Total Users"
  value={totalUsers}
  change={userChange}
  changeType={userChange > 0 ? 'positive' : 'negative'}
  icon={<UsersIcon />}
/>
```

### Accessibility Guidelines

- Provide alternative text descriptions for charts and visualizations
- Include proper titles, labels, and legends
- Ensure color choices have sufficient contrast and are distinguishable
- Consider providing tabular data as an alternative to charts
- Use ARIA attributes to enhance screen reader experience
- Support keyboard navigation for interactive visualizations

### Responsive Behavior

- Charts should resize based on container width
- Consider simplified views of complex visualizations on mobile
- Legends should reposition or switch to toggles on smaller screens
- Data tables should adapt with horizontal scrolling or responsive restructuring
- Consider stacking elements vertically on narrow viewports

## Multi-step Workflow Patterns

Multi-step workflows guide users through complex processes by breaking them into manageable steps.

### Variants

- **Linear Stepper**: Sequential steps that must be completed in order
- **Non-linear Stepper**: Steps that can be accessed in any order
- **Wizard**: Guided flow with next/back navigation
- **Branching Flow**: Workflow that adapts based on user choices

### Composition Rules

```jsx
// Linear stepper
<Stepper
  steps={steps}
  currentStepId="payment"
  isLinear={true}
  onStepChange={handleStepChange}
  onNext={handleNext}
  onBack={handleBack}
>
  <StepperContent stepId="details">
    {/* Step content */}
  </StepperContent>
  <StepperContent stepId="payment">
    {/* Step content */}
  </StepperContent>
  <StepperContent stepId="review">
    {/* Step content */}
  </StepperContent>
</Stepper>
```

### Accessibility Guidelines

- Clearly indicate current step and overall progress
- Ensure all step navigation is keyboard accessible
- Use appropriate heading structure within steps
- Provide helpful error messages for validation issues
- Use `aria-current="step"` to indicate the current step
- Consider users who may need to save progress and return later

### Responsive Behavior

- Step indicators should adapt from horizontal to vertical layout on mobile
- Content within steps should be fully responsive
- Navigation buttons should be easily accessible on mobile
- Consider condensed labels or simplified indicators on smaller screens
- Ensure touch targets are appropriately sized

## Grid and Layout Patterns

Grid systems provide consistent layout structure across the application, enhancing visual harmony and predictability.

### Variants

- **Standard Grid**: Regular column-based layout
- **Masonry Grid**: Variable height items in a grid
- **Card Grid**: Grid specifically for card layouts
- **Feature Grid**: Specialized grid for showcasing features

### Composition Rules

```jsx
// Responsive grid
<ResponsiveGrid
  columns={{ base: 1, sm: 2, md: 3, lg: 4 }}
  spacing={{ base: 'md', lg: 'lg' }}
>
  {items.map(item => (
    <GridItem key={item.id}>
      {/* Item content */}
    </GridItem>
  ))}
</ResponsiveGrid>

// Masonry grid
<MasonryGrid
  columns={{ base: 1, md: 2, lg: 3 }}
  spacing={4}
>
  {items.map(item => (
    <MasonryItem key={item.id}>
      {/* Variable height content */}
    </MasonryItem>
  ))}
</MasonryGrid>
```

### Accessibility Guidelines

- Ensure logical reading order regardless of visual layout
- Consider how grid layouts affect screen reader navigation
- Test keyboard navigation through grid items
- Use appropriate HTML semantics (e.g., lists when appropriate)
- Ensure sufficient spacing for touch interactions

### Responsive Behavior

- Grids should adapt the number of columns based on viewport width
- Column and row gaps should adjust based on screen size
- Items should reflow naturally when columns change
- Consider element stacking order when reflowing from multi-column to single-column layouts
- Use relative units (%, rem) rather than fixed units (px) for grid dimensions

## Navigation Patterns

Navigation patterns help users move through the application and understand their current location.

### Variants

- **Top Navigation**: Horizontal nav bar at the top of the page
- **Sidebar Navigation**: Vertical navigation along the side
- **Tab Navigation**: Content-level navigation using tabs
- **Mobile Navigation**: Bottom bar or drawer menu for mobile devices

### Composition Rules

```jsx
// Mobile bottom navigation
<MobileNavigation
  items={[
    { icon: <HomeIcon />, label: 'Home', path: '/' },
    { icon: <SearchIcon />, label: 'Search', path: '/search' },
    { icon: <ProfileIcon />, label: 'Profile', path: '/profile' }
  ]}
  currentPath={currentPath}
/>

// Sidebar navigation
<SidebarNav
  items={navItems}
  currentPath={currentPath}
  expandedSections={expandedSections}
  onSectionToggle={handleSectionToggle}
/>
```

### Accessibility Guidelines

- Use proper landmarks: `<nav>` elements with appropriate `aria-label`
- Clearly indicate current page/section
- Ensure keyboard navigability with logical tab order
- Use appropriate ARIA attributes for expandable sections
- Consider skip links to bypass navigation for keyboard users
- Mobile navigation should be easily operable by touch

### Responsive Behavior

- Top navigation might collapse into a hamburger menu on mobile
- Sidebar navigation should hide or convert to an overlay on small screens
- Tab navigation may switch to a dropdown or scrollable strip on mobile
- Touch targets should be at least 44px × 44px on mobile devices
- Consider gesture-based navigation for mobile interfaces

## Interaction Patterns

Interaction patterns define how users interact with elements through clicks, touches, and gestures.

### Variants

- **Touch Gestures**: Swipe, pinch, tap interactions
- **Hover Interactions**: Effects triggered on mouse hover
- **Drag and Drop**: Moving elements with mouse or touch
- **Pull to Refresh**: Mobile pattern for refreshing content

### Composition Rules

```jsx
// Swipe interaction
const { swipeHandlers } = useSwipe({
  onSwipeLeft: handleNext,
  onSwipeRight: handlePrevious,
  threshold: 50,
});

<Box {...swipeHandlers}>
  {/* Swipeable content */}
</Box>

// Pull to refresh
<PullToRefresh onRefresh={handleRefresh} threshold={100}>
  <List>
    {items.map(item => (
      <ListItem key={item.id}>{item.name}</ListItem>
    ))}
  </List>
</PullToRefresh>
```

### Accessibility Guidelines

- Provide alternative interaction methods for gesture-based features
- Ensure all interactive elements are keyboard accessible
- Use appropriate ARIA attributes to communicate interaction possibilities
- Consider users who may have motor control difficulties
- Test with assistive technologies to ensure compatibility

### Responsive Behavior

- Touch interactions should be optimized for different device sizes
- Consider viewport differences when defining interaction areas
- Hover effects should have touch equivalents on mobile devices
- Interaction hitboxes should be appropriately sized for touch on mobile
- Gesture sensitivity may need to be adjusted based on device type 