import { render, screen } from '@testing-library/react'
import { Card } from '../Card'

describe('Card', () => {
  it('renders card with children', () => {
    render(<Card>Card content</Card>)
    expect(screen.getByText('Card content')).toBeInTheDocument()
  })

  it('applies default variant classes', () => {
    const { container } = render(<Card>Content</Card>)
    const card = container.querySelector('div')
    expect(card).toHaveClass('shadow-sm', 'border', 'border-gray-200')
  })

  it('applies elevated variant classes', () => {
    const { container } = render(<Card variant="elevated">Content</Card>)
    const card = container.querySelector('div')
    expect(card).toHaveClass('shadow-md')
  })

  it('applies outlined variant classes', () => {
    const { container } = render(<Card variant="outlined">Content</Card>)
    const card = container.querySelector('div')
    expect(card).toHaveClass('border-2')
  })

  it('applies padding classes correctly', () => {
    const { container } = render(<Card padding="sm">Content</Card>)
    const card = container.querySelector('div')
    expect(card).toHaveClass('p-4')
  })

  it('applies no padding when padding is none', () => {
    const { container } = render(<Card padding="none">Content</Card>)
    const card = container.querySelector('div')
    expect(card).not.toHaveClass('p-4', 'p-6', 'p-8')
  })

  it('merges custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>)
    const card = container.querySelector('div')
    expect(card).toHaveClass('custom-class')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<Card ref={ref}>Content</Card>)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })
})
