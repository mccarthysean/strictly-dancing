---
name: Frontend Design
description: Create sophisticated, luxury UI using Tailwind CSS and shadcn/ui with Black & Gold theme. Use when designing pages, creating components, styling interfaces, implementing responsive layouts, or working on visual design. Triggers on design, UI, component, styling, shadcn, Tailwind, theme, luxury, elegant.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Frontend Design Skill

## Purpose

Build sophisticated, production-grade UI components for Strictly Dancing using Tailwind CSS v4 and shadcn/ui with a **Black & Gold luxury theme**.

## When to Use This Skill

- Designing new pages or layouts
- Creating UI components
- Styling interfaces with Tailwind
- Implementing responsive designs
- Adding shadcn/ui components
- Working on visual polish and animations
- Implementing dark mode

## Brand Identity: Black & Gold

### Design Philosophy

Strictly Dancing uses a **Black & Gold** color palette that conveys:
- **Luxury**: Premium marketplace positioning
- **Elegance**: Sophisticated dance culture
- **Trust**: Professional, established feel
- **Movement**: Gold accents suggest energy and dance

### Logo

**"The Elegant Embrace"** - Two abstract figures in a dance hold, formed by a flowing S-curve with a gold accent at the connection point.

- Light mode: Black stroke, gold accent
- Dark mode: White stroke, bright gold accent
- Location: `/frontend/public/logo.svg`, `/frontend/public/logo-dark.svg`

---

## Color System

### Primary Palette

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--background` | `#ffffff` | `#0a0a0a` | Page background |
| `--foreground` | `#0a0a0a` | `#fafafa` | Primary text |
| `--primary` | `#0a0a0a` | `#fafafa` | CTAs, primary actions |
| `--accent` | `#d4a853` | `#f0c75e` | Gold highlights, premium elements |

### Gold Palette (Premium Accents)

```css
--color-gold-50: #fefce8;   /* Subtle tints */
--color-gold-100: #fef9c3;  /* Light backgrounds */
--color-gold-200: #fef08a;  /* Hover states */
--color-gold-300: #fde047;  /* Active states */
--color-gold-400: #f0c75e;  /* Dark mode accent */
--color-gold-500: #d4a853;  /* Primary gold */
--color-gold-600: #b8860b;  /* Dark gold */
```

### Semantic Colors

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--destructive` | `#dc2626` | `#ef4444` | Errors, delete actions |
| `--success` | `#16a34a` | `#22c55e` | Success states |
| `--muted` | `#f4f4f5` | `#27272a` | Secondary backgrounds |
| `--border` | `#e4e4e7` | `#27272a` | Borders |

### Usage Rules

1. **Primary actions**: Use `bg-primary text-primary-foreground`
2. **Premium elements**: Use gold for badges, highlights, verified icons
3. **Never use gold for destructive actions**
4. **Gold text only on dark backgrounds** (contrast ratio)

---

## Typography

### Fonts

- **Display**: `Cormorant Garamond` - Headings, wordmark, luxury feel
- **Body**: `Inter` - UI, body text, excellent readability

### CSS Classes

```css
.font-display { font-family: var(--font-display); }
.font-body { font-family: var(--font-body); }
```

### Scale

| Element | Font | Size | Weight | Tailwind |
|---------|------|------|--------|----------|
| H1 | Cormorant | 3.75rem | 700 | `text-6xl font-display font-bold` |
| H2 | Cormorant | 2.25rem | 600 | `text-4xl font-display font-semibold` |
| H3 | Cormorant | 1.5rem | 600 | `text-2xl font-display font-semibold` |
| Body | Inter | 1rem | 400 | `text-base` |
| Small | Inter | 0.875rem | 400 | `text-sm` |

### Heading Pattern

```tsx
<h1 className="font-display text-6xl font-bold tracking-tight">
  Find Your Perfect Dance Host
</h1>

<h2 className="font-display text-4xl font-semibold">
  Featured Hosts
</h2>
```

---

## Component Patterns

### Buttons

```tsx
// Primary (Black)
<Button className="bg-primary text-primary-foreground hover:bg-primary/90">
  Book Now
</Button>

// Gold Accent (Premium CTA)
<Button className="bg-gold-500 text-black hover:bg-gold-600 shadow-gold">
  Become a Host
</Button>

// Outline
<Button variant="outline" className="border-border hover:bg-muted">
  Learn More
</Button>
```

### Cards

```tsx
<Card className="bg-card border-border shadow-sm hover:shadow-md transition-shadow">
  <CardHeader>
    <CardTitle className="font-display text-xl">Host Name</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
</Card>
```

### Premium/Featured Cards (with Gold)

```tsx
<Card className="bg-card border-gold-500/30 shadow-gold">
  <div className="absolute top-3 right-3">
    <Badge className="bg-gold-500 text-black">Featured</Badge>
  </div>
  {/* Content */}
</Card>
```

### Inputs

```tsx
<Input
  className="border-input bg-background focus:ring-2 focus:ring-ring"
  placeholder="Search hosts..."
/>
```

---

## Shadows

| Name | CSS | Usage |
|------|-----|-------|
| `shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle elevation |
| `shadow-md` | `0 4px 6px rgba(0,0,0,0.07)` | Cards |
| `shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modals, dropdowns |
| `shadow-gold` | `0 4px 20px rgba(212,168,83,0.25)` | Premium elements |
| `shadow-elegant` | `0 0 40px rgba(212,168,83,0.15)` | Ambient gold glow |

---

## Animations

### Transitions

```tsx
// Standard transition
<div className="transition-all duration-300 ease-out">

// Elegant hover (cubic-bezier)
<div className="transition-elegant">
```

### Keyframes Available

- `fade-in` - Opacity 0 to 1
- `slide-up` - Slide up with fade
- `shimmer` - Loading shimmer effect

### Hover Patterns

```tsx
// Card hover
<Card className="hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">

// Button hover
<Button className="hover:scale-[1.02] active:scale-[0.98] transition-transform">
```

---

## Dark Mode

### Implementation

Dark mode is controlled via the `.dark` class on `<html>`.

```tsx
// Toggle dark mode
document.documentElement.classList.toggle('dark')

// Check current mode
const isDark = document.documentElement.classList.contains('dark')
```

### Color Switching

All colors automatically switch via CSS variables. Use semantic tokens:

```tsx
// GOOD - Uses CSS variables, auto-switches
<div className="bg-background text-foreground">

// BAD - Hardcoded colors
<div className="bg-white text-black">
```

### Logo Switching

```tsx
const Logo = () => {
  const isDark = useIsDarkMode()
  return (
    <img
      src={isDark ? '/logo-dark.svg' : '/logo.svg'}
      alt="Strictly Dancing"
    />
  )
}
```

---

## Responsive Design

### Breakpoints

| Breakpoint | Min Width | Usage |
|------------|-----------|-------|
| `sm` | 640px | Large phones |
| `md` | 768px | Tablets |
| `lg` | 1024px | Laptops |
| `xl` | 1280px | Desktops |
| `2xl` | 1536px | Large screens |

### Mobile-First Pattern

```tsx
<div className="
  px-4 py-6
  md:px-6 md:py-8
  lg:px-8 lg:py-12
">
  <h1 className="
    text-3xl
    md:text-4xl
    lg:text-6xl
    font-display font-bold
  ">
    Welcome
  </h1>
</div>
```

### Container

```tsx
<div className="container mx-auto px-4 max-w-7xl">
  {/* Content */}
</div>
```

---

## Accessibility

### Focus States

All interactive elements have visible focus via `focus-visible:ring-2 focus-visible:ring-ring`.

### Color Contrast

- Text on backgrounds: Minimum 4.5:1 contrast ratio
- Gold on white: Use `gold-600` or darker for text
- Gold on black: Use `gold-400` or lighter for text

### ARIA Patterns

```tsx
// Loading state
<Button disabled aria-busy="true">
  <span className="animate-spin">...</span>
  Loading
</Button>

// Icon buttons
<Button size="icon" aria-label="Close menu">
  <X className="h-4 w-4" />
</Button>
```

---

## File Structure

```
frontend/
├── src/
│   ├── index.css              # Tailwind + design tokens
│   ├── lib/
│   │   └── utils.ts           # cn() utility
│   └── components/
│       └── ui/                # shadcn components
├── public/
│   ├── logo.svg               # Light mode logo
│   ├── logo-dark.svg          # Dark mode logo
│   ├── logo-icon.svg          # Icon only
│   └── favicon.svg            # Browser favicon
└── tailwind.config.ts         # (Tailwind v4 uses CSS config)
```

---

## Quick Reference

### Import cn() Utility

```tsx
import { cn } from '@/lib/utils'

<div className={cn(
  'base-classes',
  condition && 'conditional-class',
  className
)}>
```

### Common Patterns

```tsx
// Hero section
<section className="py-20 md:py-32 bg-background">
  <div className="container mx-auto px-4 text-center">
    <h1 className="font-display text-5xl md:text-7xl font-bold mb-6">
      Title
    </h1>
    <p className="text-muted-foreground text-lg md:text-xl max-w-2xl mx-auto">
      Description
    </p>
  </div>
</section>

// Feature card grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {features.map(feature => (
    <Card key={feature.id}>...</Card>
  ))}
</div>

// Gold badge
<Badge className="bg-gold-500 text-black font-medium">
  Verified Host
</Badge>
```

---

## Integration

This skill automatically activates when:
- Creating UI components
- Styling with Tailwind CSS
- Working with shadcn/ui
- Implementing designs
- Adding animations or transitions
- Working on responsive layouts
