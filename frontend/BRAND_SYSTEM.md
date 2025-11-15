# 🎨 CASTOR BRAND SYSTEM

## Color Palette

### Primary Colors
```css
--castor-blue-50: #eff6ff;
--castor-blue-100: #dbeafe;
--castor-blue-200: #bfdbfe;
--castor-blue-300: #93c5fd;
--castor-blue-400: #60a5fa;
--castor-blue-500: #3b82f6; /* Primary */
--castor-blue-600: #2563eb; /* Primary Dark */
--castor-blue-700: #1d4ed8;
--castor-blue-800: #1e40af;
--castor-blue-900: #1e3a8a;
```

### Secondary Colors
```css
--castor-green-500: #10b981; /* Success, Growth */
--castor-green-600: #059669;
--castor-green-700: #047857;

--castor-purple-500: #8b5cf6; /* Premium, Agency */
--castor-purple-600: #7c3aed;
--castor-purple-700: #6d28d9;

--castor-orange-500: #f59e0b; /* Energy, CTA */
--castor-orange-600: #d97706;
--castor-orange-700: #b45309;
```

### Semantic Colors
```css
--castor-success: #10b981;
--castor-warning: #f59e0b;
--castor-error: #ef4444;
--castor-info: #3b82f6;
```

### Data Visualization Colors
```css
/* For charts - accessible, colorblind-friendly */
--data-1: #3b82f6; /* Blue */
--data-2: #10b981; /* Green */
--data-3: #f59e0b; /* Orange */
--data-4: #8b5cf6; /* Purple */
--data-5: #ec4899; /* Pink */
--data-6: #06b6d4; /* Cyan */
```

## Typography

### Font Family
- **Primary:** Inter (Google Fonts)
- **Fallback:** system-ui, -apple-system, sans-serif

### Type Scale
```css
/* Display - Hero headlines */
.text-display {
  font-size: 3rem;      /* 48px */
  line-height: 1.167;   /* 56px */
  font-weight: 700;
  letter-spacing: -0.02em;
}

/* H1 - Page titles */
.text-h1 {
  font-size: 2.25rem;   /* 36px */
  line-height: 1.222;   /* 44px */
  font-weight: 700;
  letter-spacing: -0.01em;
}

/* H2 - Section headers */
.text-h2 {
  font-size: 1.875rem;  /* 30px */
  line-height: 1.267;   /* 38px */
  font-weight: 600;
}

/* H3 - Subsections */
.text-h3 {
  font-size: 1.5rem;    /* 24px */
  line-height: 1.333;  /* 32px */
  font-weight: 600;
}

/* Body - Default text */
.text-body {
  font-size: 1rem;      /* 16px */
  line-height: 1.5;     /* 24px */
  font-weight: 400;
}

/* Small - Captions, labels */
.text-small {
  font-size: 0.875rem;  /* 14px */
  line-height: 1.429;   /* 20px */
  font-weight: 400;
}
```

## Spacing Scale

```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
```

## Component Styles

### Buttons

#### Primary Button
```tsx
<button className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl">
  Primary Action
</button>
```

#### Secondary Button
```tsx
<button className="px-6 py-3 bg-white text-blue-600 font-semibold rounded-lg border-2 border-blue-600 hover:bg-blue-50 transition-colors">
  Secondary Action
</button>
```

#### Ghost Button
```tsx
<button className="px-6 py-3 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors">
  Ghost Action
</button>
```

### Cards

#### Metric Card
```tsx
<div className="bg-white rounded-lg shadow p-6">
  <div className="text-sm text-gray-600 mb-1">Label</div>
  <div className="text-3xl font-bold text-gray-900">Value</div>
  <div className="text-sm text-green-600 mt-2">+12% change</div>
</div>
```

#### Podcast Card
```tsx
<div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-6">
  {/* Card content */}
</div>
```

### Badges

#### Status Badge
```tsx
<span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
  Verified
</span>
```

#### Category Badge
```tsx
<span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
  Technology
</span>
```

## Shadows

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
```

## Border Radius

```css
--radius-sm: 0.25rem;   /* 4px */
--radius: 0.5rem;       /* 8px */
--radius-md: 0.75rem;   /* 12px */
--radius-lg: 1rem;      /* 16px */
--radius-xl: 1.5rem;    /* 24px */
--radius-full: 9999px;
```

## Motion Design

### Transitions
```css
--transition-fast: 150ms ease-in-out;
--transition-base: 200ms ease-in-out;
--transition-slow: 300ms ease-in-out;
```

### Animations
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

## Accessibility

### Focus States
```css
.focus-ring {
  outline: 2px solid transparent;
  outline-offset: 2px;
}

.focus-ring:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
```

### Color Contrast
- All text meets WCAG AA standards (4.5:1 for normal text, 3:1 for large text)
- Interactive elements have clear focus indicators
- Color is never the only indicator of state

## Usage Guidelines

### Do's ✅
- Use primary blue for main CTAs and branding
- Use green for success states and positive metrics
- Use purple for premium/agency features
- Use orange for energy/attention-grabbing elements
- Maintain consistent spacing using the scale
- Use shadows to create depth hierarchy
- Ensure sufficient color contrast

### Don'ts ❌
- Don't use more than 3 colors in a single component
- Don't mix different border radius sizes unnecessarily
- Don't use shadows excessively (max 2 levels deep)
- Don't use color alone to convey information
- Don't use font sizes outside the type scale
- Don't create custom spacing values

---

**Last Updated:** 2025-01-13
