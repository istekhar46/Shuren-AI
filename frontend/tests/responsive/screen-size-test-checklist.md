# Screen Size Testing Checklist

## Overview
This checklist ensures the onboarding chat interface works correctly across all screen sizes and devices.

## Test Environments

### Mobile Devices (< 768px)
- [ ] iPhone SE (375x667)
- [ ] iPhone 12/13 (390x844)
- [ ] iPhone 14 Pro Max (430x932)
- [ ] Samsung Galaxy S21 (360x800)
- [ ] Samsung Galaxy S21 Ultra (412x915)

### Tablet Devices (768px - 1024px)
- [ ] iPad Mini (768x1024)
- [ ] iPad Air (820x1180)
- [ ] iPad Pro 11" (834x1194)
- [ ] Samsung Galaxy Tab (800x1280)

### Desktop Screens (> 1024px)
- [ ] Laptop (1366x768)
- [ ] Desktop HD (1920x1080)
- [ ] Desktop Full HD (2560x1440)
- [ ] Ultrawide (3440x1440)

## Component Testing

### AgentHeader
#### Mobile (< 768px)
- [ ] Agent icon displays at appropriate size (text-4xl)
- [ ] Agent name is readable and doesn't overflow
- [ ] Agent description wraps properly
- [ ] State indicator shows in mobile layout (sm:hidden section)
- [ ] Step counter displays correctly ("Step X of 9")
- [ ] Header is sticky at top
- [ ] Background color is visible (purple-600)
- [ ] Padding is appropriate for touch targets

#### Tablet (768px - 1024px)
- [ ] Desktop layout is used (hidden sm:flex)
- [ ] Agent icon and text are properly aligned
- [ ] State indicator shows in desktop format
- [ ] All elements fit without horizontal scroll

#### Desktop (> 1024px)
- [ ] Full desktop layout displays
- [ ] All spacing is appropriate
- [ ] Text is easily readable
- [ ] No layout shifts or jumps

### OnboardingProgressBar
#### Mobile (< 768px)
- [ ] Progress bar is hidden on mobile (hidden lg:block)
- [ ] No horizontal overflow
- [ ] Progress percentage visible in header

#### Tablet (768px - 1024px)
- [ ] Progress bar is hidden on tablet (hidden lg:block)
- [ ] Layout remains clean without sidebar

#### Desktop (> 1024px)
- [ ] Sidebar displays on left (lg:w-80)
- [ ] Progress bar shows all 9 states
- [ ] Current state is highlighted
- [ ] Completed states show checkmarks
- [ ] State names are readable
- [ ] Scrollable if content overflows
- [ ] Fixed width (320px / 20rem)

### Chat Messages
#### Mobile (< 768px)
- [ ] Messages take full width
- [ ] User messages align right
- [ ] Assistant messages align left
- [ ] Message bubbles have appropriate padding
- [ ] Text wraps properly
- [ ] Timestamps are visible
- [ ] Streaming indicator displays correctly
- [ ] No horizontal scroll

#### Tablet (768px - 1024px)
- [ ] Messages are centered with max-width
- [ ] Proper spacing between messages
- [ ] Readable font sizes

#### Desktop (> 1024px)
- [ ] Messages centered with max-width (max-w-4xl)
- [ ] Proper spacing and padding
- [ ] Easy to read and scan

### MessageInput
#### Mobile (< 768px)
- [ ] Input takes full width
- [ ] Touch target is large enough (min 44px height)
- [ ] Keyboard doesn't obscure input
- [ ] Send button is accessible
- [ ] Placeholder text is visible
- [ ] Disabled state is clear

#### Tablet (768px - 1024px)
- [ ] Input is appropriately sized
- [ ] Comfortable typing experience

#### Desktop (> 1024px)
- [ ] Input is centered with max-width
- [ ] Keyboard shortcuts work (Enter to send)

### PlanPreviewCard
#### Mobile (< 768px)
- [ ] Modal takes full screen or slides from bottom
- [ ] Close button (X) is easily tappable
- [ ] Content is scrollable
- [ ] Approve/Modify buttons are accessible
- [ ] Text is readable
- [ ] No horizontal overflow

#### Tablet (768px - 1024px)
- [ ] Modal is centered and sized appropriately
- [ ] Content fits well
- [ ] Buttons are properly sized

#### Desktop (> 1024px)
- [ ] Modal is centered with appropriate width
- [ ] Content is well-formatted
- [ ] Easy to read and interact with

### WorkoutPlanPreview
#### All Screen Sizes
- [ ] Plan summary displays clearly
- [ ] Equipment list is readable
- [ ] Day-by-day breakdown is organized
- [ ] Exercise details (sets, reps, rest) are clear
- [ ] Notes are visible if present
- [ ] No text overflow
- [ ] Proper spacing between sections

### MealPlanPreview
#### All Screen Sizes
- [ ] Calorie target is prominent
- [ ] Macro breakdown is clear
- [ ] Sample meals are well-formatted
- [ ] Nutrition info per meal is readable
- [ ] Meal timing is visible
- [ ] Dietary restrictions are noted
- [ ] No text overflow

## Interaction Testing

### Touch Interactions (Mobile/Tablet)
- [ ] All buttons have adequate touch targets (min 44x44px)
- [ ] Tap feedback is visible
- [ ] Scrolling is smooth
- [ ] No accidental taps
- [ ] Swipe gestures work if implemented

### Mouse Interactions (Desktop)
- [ ] Hover states are visible
- [ ] Click targets are clear
- [ ] Cursor changes appropriately
- [ ] Tooltips display if present

### Keyboard Navigation (All Sizes)
- [ ] Tab order is logical
- [ ] Focus indicators are visible
- [ ] Enter sends message
- [ ] Escape closes modals
- [ ] No keyboard traps

## Layout Testing

### Orientation Changes
- [ ] Portrait to landscape transition is smooth
- [ ] No layout breaks on rotation
- [ ] Content remains accessible

### Zoom Levels
- [ ] 100% zoom - default layout works
- [ ] 150% zoom - layout adapts properly
- [ ] 200% zoom - content remains accessible
- [ ] No horizontal scroll at any zoom level

### Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

## Performance Testing

### Load Times
- [ ] Initial render < 2 seconds on mobile
- [ ] Initial render < 1 second on desktop
- [ ] Smooth animations on all devices

### Scrolling Performance
- [ ] Smooth scrolling on mobile
- [ ] No jank or stuttering
- [ ] Lazy loading works if implemented

## Accessibility Testing

### Screen Readers
- [ ] VoiceOver (iOS/macOS) - all content accessible
- [ ] TalkBack (Android) - all content accessible
- [ ] NVDA (Windows) - all content accessible
- [ ] JAWS (Windows) - all content accessible

### Color Contrast
- [ ] Text meets WCAG AA standards (4.5:1)
- [ ] Interactive elements are distinguishable
- [ ] Focus indicators are visible

## Edge Cases

### Long Content
- [ ] Long agent descriptions wrap properly
- [ ] Long messages don't break layout
- [ ] Long plan details are scrollable
- [ ] Long state names are truncated or wrapped

### Empty States
- [ ] No messages - empty state displays
- [ ] Loading state - spinner shows
- [ ] Error state - error message displays

### Network Conditions
- [ ] Slow 3G - graceful degradation
- [ ] Offline - appropriate error message
- [ ] Intermittent connection - retry logic works

## Sign-off

### Tester Information
- Tester Name: _______________
- Date: _______________
- Environment: _______________

### Results
- [ ] All mobile tests passed
- [ ] All tablet tests passed
- [ ] All desktop tests passed
- [ ] All interaction tests passed
- [ ] All accessibility tests passed
- [ ] All edge cases handled

### Issues Found
1. _______________
2. _______________
3. _______________

### Notes
_______________
_______________
_______________
