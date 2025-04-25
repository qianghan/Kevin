# KAI UI Responsive Design Principles

## Core Principles

### Mobile-First Approach
Design for the smallest screens first, then progressively enhance the experience for larger screens. This approach ensures that core functionality is available to all users regardless of device, and helps prioritize content effectively.

### Content Prioritization
- Identify and maintain focus on core content and functionality across all devices
- Progressively disclose secondary content as screen size increases
- Maintain the same content availability across devices, but adapt presentation

### Consistency Across Devices
- Maintain brand and design consistency across all breakpoints
- Ensure UI patterns are recognizable even when their layout changes
- Use the same visual language, terminology, and interaction patterns

### Performance Optimization
- Optimize images and assets for different screen sizes
- Implement lazy loading for off-screen content
- Minimize unnecessary animations on mobile devices
- Target sub-3 second initial load times for all devices

## Breakpoint System

### Standard Breakpoints
Our system uses the following breakpoints:

| Name | Size Range | Typical Devices |
|------|------------|----------------|
| xs   | 0-599px    | Mobile phones  |
| sm   | 600-959px  | Tablets, large phones |
| md   | 960-1279px | Small laptops, tablets in landscape |
| lg   | 1280-1919px | Laptops, desktops |
| xl   | 1920px+    | Large screens, TVs |

### Breakpoint Usage
- Avoid creating layouts specifically for a single device model
- Test designs at the edges of each breakpoint range
- For complex layouts, consider intermediate breakpoints
- Use em/rem units for breakpoints to respect user font size preferences

## Layout Shifts

### Grid System Adaptation
The 12-column grid adapts across breakpoints:
- **Mobile (xs)**: 4-column grid with 8px gutters
- **Tablet (sm)**: 8-column grid with 16px gutters
- **Desktop (md+)**: 12-column grid with 24px gutters

### Content Reflow Patterns
When adapting from desktop to mobile:

1. **Stacking**
   ```
   Desktop: [A] [B] [C]
   Mobile:  [A]
            [B]
            [C]
   ```

2. **Accordion/Disclosure**
   ```
   Desktop: [Title] [Content visible]
   Mobile:  [Title ▼] (tap to expand)
            [Content hidden by default]
   ```

3. **Horizontal to Vertical Navigation**
   ```
   Desktop: [Home] [Products] [About] [Contact]
   Mobile:  [☰] → expands to vertical menu
   ```

4. **Sidebar to Off-canvas**
   ```
   Desktop: [Sidebar] | [Main Content]
   Mobile:  [Main Content] (Sidebar hidden off-canvas)
   ```

### Priority Shifting

Adjust content priority based on context:
- Move primary actions to thumb-friendly areas on mobile
- Consider different navigation patterns for different devices
- Ensure CTAs remain prominent at all breakpoints

## Component Adaptations

### Buttons
- Maintain minimum touch target size of 44x44px on mobile
- Consider expanded full-width buttons for primary actions on small screens
- Maintain consistent padding-to-text ratio across sizes

### Navigation
- Desktop: Horizontal navigation bar with dropdowns
- Tablet: Horizontal navigation with condensed options
- Mobile: Off-canvas menu or bottom navigation bar

### Cards
- Desktop: Multi-column grid with hover states
- Mobile: Single column with touch states

### Tables
- Desktop: Full table with all columns
- Mobile: Responsive tables that either:
  - Allow horizontal scrolling
  - Stack columns vertically
  - Hide less important columns
  - Provide expandable rows

### Forms
- Stack form elements vertically on mobile
- Use full-width inputs on small screens
- Consider multi-step forms for complex interactions on mobile

## Visual Examples

### Desktop Layout
```
┌─────────────────────────────────────────────────────────┐
│ [Logo]      [Navigation]               [Search] [Profile]│
├─────────────────┬───────────────────────────────────────┤
│                 │                                       │
│                 │                                       │
│  Sidebar        │  Main Content Area                    │
│  Navigation     │                                       │
│                 │  ┌─────────┐  ┌─────────┐  ┌─────────┐│
│  [Link 1]       │  │ Card 1  │  │ Card 2  │  │ Card 3  ││
│  [Link 2]       │  └─────────┘  └─────────┘  └─────────┘│
│  [Link 3]       │                                       │
│  [Link 4]       │  ┌─────────┐  ┌─────────┐  ┌─────────┐│
│                 │  │ Card 4  │  │ Card 5  │  │ Card 6  ││
│                 │  └─────────┘  └─────────┘  └─────────┘│
└─────────────────┴───────────────────────────────────────┘
```

### Tablet Layout
```
┌─────────────────────────────────────────┐
│ [Logo]  [Navigation]        [Profile]   │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐       │
│  │ Card 1      │  │ Card 2      │       │
│  └─────────────┘  └─────────────┘       │
│                                         │
│  ┌─────────────┐  ┌─────────────┐       │
│  │ Card 3      │  │ Card 4      │       │
│  └─────────────┘  └─────────────┘       │
│                                         │
│  ┌─────────────┐  ┌─────────────┐       │
│  │ Card 5      │  │ Card 6      │       │
│  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────┘
```

### Mobile Layout
```
┌───────────────────────┐
│ [☰] [Logo]  [Profile] │
├───────────────────────┤
│  ┌─────────────────┐  │
│  │ Card 1          │  │
│  └─────────────────┘  │
│                       │
│  ┌─────────────────┐  │
│  │ Card 2          │  │
│  └─────────────────┘  │
│                       │
│  ┌─────────────────┐  │
│  │ Card 3          │  │
│  └─────────────────┘  │
│                       │
│  ┌─────────────────┐  │
│  │ Card 4          │  │
│  └─────────────────┘  │
│                       │
│  ┌─────────────────┐  │
│  │ Card 5          │  │
│  └─────────────────┘  │
│                       │
│  ┌─────────────────┐  │
│  │ Card 6          │  │
│  └─────────────────┘  │
├───────────────────────┤
│ [Home] [Search] [Menu]│
└───────────────────────┘
```

## Testing Strategy

### Cross-Device Testing
- Test on actual devices when possible, not just browser simulations
- Use a device lab with common device types and sizes
- Test both landscape and portrait orientations

### Performance Metrics
- Page load time
- Time to interactive
- Cumulative layout shift (CLS)
- First contentful paint (FCP)
- Largest contentful paint (LCP)

### Accessibility Considerations
- Test with screen readers across device types
- Ensure touch targets are adequately sized on mobile
- Verify keyboard navigation works on desktop
- Check content readability at different zoom levels

### Browser Compatibility
- Test across major browsers including older versions
- Implement graceful degradation for unsupported features
- Use feature detection instead of browser detection

## Implementation Guidelines

### CSS Approach
- Use responsive units (rem, em, %) over fixed units (px)
- Implement CSS Grid and Flexbox for flexible layouts
- Use media queries consistently
- Consider a mobile-first CSS architecture:

```css
/* Mobile first (base styles) */
.element {
  width: 100%;
}

/* Tablet up */
@media (min-width: 600px) {
  .element {
    width: 50%;
  }
}

/* Desktop up */
@media (min-width: 960px) {
  .element {
    width: 33.333%;
  }
}
```

### Component Best Practices
- Build components with responsive behavior built in
- Use props to control responsive behavior when needed:

```jsx
<Grid 
  columns={{
    xs: 1,
    sm: 2,
    md: 3,
    lg: 4
  }} 
  spacing={{
    xs: '8px',
    md: '16px',
    lg: '24px'
  }}
>
  {/* Grid content */}
</Grid>
```

- Utilize responsive hooks in components:

```jsx
const isMobile = useBreakpointValue({ base: true, md: false });

return (
  <div>
    {isMobile ? <MobileView /> : <DesktopView />}
  </div>
);
```

## Responsive Design Checklist

- [ ] Design starts from mobile and expands to larger screens
- [ ] All interactive elements have adequate touch targets
- [ ] Content priority is maintained across breakpoints
- [ ] No horizontal scrolling on standard content
- [ ] Typography is readable at all screen sizes
- [ ] Images are optimized for different screen sizes
- [ ] Forms are usable on touch devices
- [ ] Navigation is accessible on all devices
- [ ] Performance is tested on low-end devices
- [ ] All content is accessible regardless of screen size
- [ ] Responsive behavior is smooth without jarring transitions 