# Feature Blueprint: New Frontend Page/Component

Use this template when creating a new frontend feature.

## Steps

### 1. Create Page

Create `frontend/app/[feature]/page.tsx`:

```typescript
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

export default function [Feature]Page() {
  const queryClient = useQueryClient();
  
  // Fetch data
  const { data, isLoading, error } = useQuery({
    queryKey: ['[feature-plural]'],
    queryFn: async () => {
      const res = await fetch('/api/v1/[feature-plural]');
      if (!res.ok) throw new Error('Failed to fetch');
      return res.json();
    }
  });
  
  // Mutations
  const createMutation = useMutation({
    mutationFn: async (data: [Feature]Create) => {
      const res = await fetch('/api/v1/[feature-plural]', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!res.ok) throw new Error('Failed to create');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['[feature-plural]'] });
    }
  });
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      <h1>[Feature] Page</h1>
      {/* Implementation */}
    </div>
  );
}
```

### 2. Create Component (if reusable)

Create `frontend/components/[feature]/[Feature]Card.tsx`:

```typescript
interface [Feature]CardProps {
  [feature]: {
    id: string;
    name: string;
    description?: string;
  };
  onEdit?: () => void;
  onDelete?: () => void;
}

export function [Feature]Card({ [feature], onEdit, onDelete }: [Feature]CardProps) {
  return (
    <div className="card">
      <h3>{[feature].name}</h3>
      {[feature].description && <p>{[feature].description}</p>}
      {/* Actions */}
    </div>
  );
}
```

### 3. Add Types

Add to `frontend/types/[feature].ts`:

```typescript
export interface [Feature] {
  id: string;
  name: string;
  description?: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface [Feature]Create {
  name: string;
  description?: string;
}

export interface [Feature]Update {
  name?: string;
  description?: string;
}
```

### 4. Add API Hooks (optional)

Create `frontend/hooks/use[Feature].ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { [Feature], [Feature]Create, [Feature]Update } from '@/types/[feature]';

export function use[Feature-plural]() {
  return useQuery<[Feature][]>({
    queryKey: ['[feature-plural]'],
    queryFn: async () => {
      const res = await fetch('/api/v1/[feature-plural]');
      return res.json();
    }
  });
}

export function useCreate[Feature]() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: [Feature]Create) => {
      const res = await fetch('/api/v1/[feature-plural]', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['[feature-plural]'] });
    }
  });
}
```

### 5. Add Tests

Create `frontend/components/[feature]/__tests__/[Feature]Card.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react';
import { [Feature]Card } from '../[Feature]Card';

describe('[Feature]Card', () => {
  it('renders [feature] information', () => {
    const [feature] = {
      id: '1',
      name: 'Test [Feature]',
      description: 'Test description'
    };
    
    render(<[Feature]Card [feature]={[feature]} />);
    
    expect(screen.getByText('Test [Feature]')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });
});
```

### 6. Update Navigation (if needed)

Add to navigation component:

```typescript
{
  name: '[Feature]',
  href: '/[feature]',
  icon: [Icon]
}
```

### 7. Checklist

- [ ] Page created
- [ ] Components created (if needed)
- [ ] Types defined
- [ ] API hooks created (if needed)
- [ ] Tests written
- [ ] Navigation updated (if needed)
- [ ] Error handling implemented
- [ ] Loading states handled
- [ ] Responsive design verified
- [ ] Accessibility checked
