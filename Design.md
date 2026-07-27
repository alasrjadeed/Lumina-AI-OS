# Lumina AI OS — Design System

> **Version**: 1.0.0 | **Status**: Living Document | **Updated**: July 2026

---

## 1. Design Philosophy

Lumina's design system is built on three principles:

1. **Clarity**: Every element should communicate its purpose instantly. No decoration without function.
2. **Efficiency**: Power users need speed. Keyboard shortcuts, slash commands, and dense information layouts.
3. **Accessibility**: WCAG 2.1 AA compliance. Keyboard navigable, screen-reader friendly, high contrast.

---

## 2. Color System

### 2.1 Brand Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | `#6366F1` (Indigo 500) | Primary actions, links, focus rings |
| `--color-primary-light` | `#818CF8` (Indigo 400) | Hover states, secondary accents |
| `--color-primary-dark` | `#4F46E5` (Indigo 600) | Active states, pressed buttons |

### 2.2 Surface Colors (Light Mode)

| Token | Value | Usage |
|-------|-------|-------|
| `--color-bg` | `#0F0F13` | Main background |
| `--color-surface` | `#1A1A24` | Cards, panels, sidebar |
| `--color-surface-hover` | `#24243A` | Hover states |
| `--color-surface-active` | `#2E2E4A` | Active/selected states |
| `--color-border` | `#2E2E4A` | Borders and dividers |

### 2.3 Text Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--color-text` | `#F1F1F9` | Primary text |
| `--color-text-secondary` | `#A0A0B8` | Secondary text, descriptions |
| `--color-text-muted` | `#6B6B80` | Tertiary text, placeholders |

### 2.4 Semantic Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--color-success` | `#22C55E` (Green 500) | Success states, connected status |
| `--color-warning` | `#F59E0B` (Amber 500) | Warnings, degraded states |
| `--color-error` | `#EF4444` (Red 500) | Errors, disconnected status |
| `--color-info` | `#3B82F6` (Blue 500) | Info messages, links |

---

## 3. Typography

### 3.1 Font Stack

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
font-family: 'JetBrains Mono', 'Fira Code', monospace; /* Code blocks */
```

### 3.2 Type Scale

| Token | Size / Line Height | Usage |
|-------|-------------------|-------|
| `text-xs` | 12px / 16px | Labels, badges, captions |
| `text-sm` | 14px / 20px | Secondary text, descriptions |
| `text-base` | 16px / 24px | Body text, inputs |
| `text-lg` | 18px / 28px | Subtitles, card titles |
| `text-xl` | 20px / 28px | Section headers |
| `text-2xl` | 24px / 32px | Page titles |
| `text-3xl` | 30px / 36px | Hero headings |
| `text-4xl` | 36px / 40px | Landing page headings |

### 3.3 Font Weights

| Token | Value | Usage |
|-------|-------|-------|
| `font-normal` | 400 | Body text |
| `font-medium` | 500 | Interactive text, labels |
| `font-semibold` | 600 | Headings, emphasis |
| `font-bold` | 700 | Primary headings |

---

## 4. Spacing System

Based on a 4px grid. All spacing uses Tailwind's default scale.

| Token | Value | Usage |
|-------|-------|-------|
| `p-1` / `gap-1` | 4px | Tight spacing, icon + text |
| `p-2` / `gap-2` | 8px | Compact layouts |
| `p-3` / `gap-3` | 12px | Default card padding |
| `p-4` / `gap-4` | 16px | Section padding |
| `p-6` / `gap-6` | 24px | Page padding |
| `p-8` / `gap-8` | 32px | Large sections |
| `p-12` | 48px | Hero sections |

---

## 5. Component Library

### 5.1 Card

```tsx
<Card>
  <CardSection title="Section Title">
    {/* Content */}
  </CardSection>
</Card>
```

- Background: `--color-surface`
- Border: 1px `--color-border`, radius: 8px
- Padding: 24px
- Hover: slight border brighten

### 5.2 Button Variants

| Variant | Classes | Usage |
|---------|---------|-------|
| Primary | `bg-indigo-500 hover:bg-indigo-600 text-white` | Main actions |
| Secondary | `bg-surface hover:bg-surface-hover text-text border` | Secondary actions |
| Ghost | `hover:bg-surface-hover text-text` | Minimal actions |
| Danger | `bg-red-500 hover:bg-red-600 text-white` | Destructive actions |

### 5.3 Input

```tsx
<input className="w-full bg-surface border border-border rounded-lg px-4 py-2.5
                    text-text placeholder:text-text-muted
                    focus:outline-none focus:ring-2 focus:ring-indigo-500
                    focus:border-transparent" />
```

### 5.4 Loading States

```tsx
// Skeleton loading
<SkeletonCard />  // 3 animated lines
<SkeletonLine />  // 1 animated line

// Spinner
<LoadingSpinner />  // Animated SVG spinner

// Full page states
<LoadingState />    // Centered spinner
<EmptyState />      // Icon + message for empty data
<ErrorState />      // Icon + message + retry button for errors
```

### 5.5 Toast Notifications

```tsx
// Usage
const { addToast } = useToast();
addToast("Message sent successfully", "success");

// Variants
// success (green), error (red), warning (amber), info (blue)
```

### 5.6 Page Header

```tsx
<PageHeader
  title="Page Title"
  description="Optional description text"
  actions={<Button>Action</Button>}
/>
```

---

## 6. Layout System

### 6.1 App Shell

```
┌─────────────────────────────────────────────────────┐
│ ┌──────────┐ ┌────────────────────────────────────┐ │
│ │          │ │  Header (PageHeader)                │ │
│ │ Sidebar  │ ├────────────────────────────────────┤ │
│ │          │ │                                    │ │
│ │  Nav     │ │  Content Area                      │ │
│ │  Links   │ │  (Page Content)                    │ │
│ │          │ │                                    │ │
│ └──────────┘ └────────────────────────────────────┘ │
│              ┌────────────────────────────────────┐ │
│              │  Toast Container (fixed, bottom-r)  │ │
│              └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 6.2 Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 768px | Full-width, hamburger menu |
| Tablet | 768px - 1024px | Collapsed sidebar |
| Desktop | > 1024px | Full sidebar + content |

### 6.3 Sidebar Navigation

- **Width**: 256px (expanded), 64px (collapsed)
- **Sections**: Main (Dashboard, Chat, Agents), Tools (Code, Browser, Desktop), Business (CRM, SEO, Marketing), System (Settings, About)
- **Active state**: Indigo highlight with left border accent
- **Collapsible**: Via hamburger button on mobile, toggle on desktop

---

## 7. Icon System

- **Library**: lucide-react (MIT licensed, 1000+ icons)
- **Sizes**: 16px (inline), 20px (UI), 24px (navigation), 32px (hero)
- **Color**: Inherits from parent text color
- **Usage**: Always paired with text labels unless universally recognized

---

## 8. Motion & Animation

| Property | Duration | Easing | Usage |
|----------|----------|--------|-------|
| `transition-all` | 150ms | `ease-in-out` | Hover states, focus rings |
| `transition-all` | 200ms | `ease-out` | Modal open/close |
| `transition-all` | 300ms | `ease-in-out` | Sidebar collapse/expand |
| `animate-spin` | 1s linear infinite | `linear` | Loading spinners |
| `animate-pulse` | 2s cubic-bezier infinite | — | Skeleton loading |

---

## 9. Dark Mode (Default)

Lumina uses dark mode as the default theme. All color tokens are designed for dark backgrounds with high contrast ratios.

### Contrast Ratios (WCAG AA)

| Element | Ratio | Status |
|---------|-------|--------|
| Body text on background | 15.2:1 | AAA |
| Secondary text on background | 7.5:1 | AAA |
| Primary button text | 4.6:1 | AA |
| Indigo on dark surface | 4.9:1 | AA |

---

## 10. Accessibility Checklist

- [x] All interactive elements are keyboard focusable
- [x] Focus rings are visible (2px indigo-500 ring)
- [x] Icons have `aria-hidden="true"` with text labels
- [x] Forms have proper `<label>` associations
- [x] Error messages are associated with inputs via `aria-describedby`
- [x] Toast notifications use `role="alert"` and `aria-live="polite"`
- [x] Loading states announced via `aria-busy="true"`
- [x] Color is never the sole indicator of state (icons + text)
- [x] Touch targets are minimum 44x44px

---

## 11. Component Workflow

When building a new UI component:

1. **Check existing** — Look in `src/components/ui/` for reusable primitives
2. **Use tokens** — Reference design tokens, never hardcode colors
3. **Responsive first** — Design for mobile, enhance for desktop
4. **Loading + Empty + Error** — Every data component needs all three states
5. **Accessibility** — Run axe DevTools before committing
6. **Performance** — Lazy load below-the-fold, use `React.memo()` for pure components

---

## 12. Tailwind Configuration

```js
// tailwind.config.ts
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          400: "#818CF8",
          500: "#6366F1",
          600: "#4F46E5",
        },
        surface: {
          DEFAULT: "#1A1A24",
          hover: "#24243A",
          active: "#2E2E4A",
        },
        background: "#0F0F13",
        border: "#2E2E4A",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      borderRadius: {
        DEFAULT: "8px",
      },
    },
  },
  plugins: [],
};
```
