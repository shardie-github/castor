import { render, screen } from '@testing-library/react'
import { EmptyState } from '../EmptyState'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

describe('EmptyState', () => {
  it('renders title', () => {
    render(<EmptyState title="No data" />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })

  it('renders description when provided', () => {
    render(<EmptyState title="No data" description="There is no data to display" />)
    expect(screen.getByText('There is no data to display')).toBeInTheDocument()
  })

  it('does not render description when not provided', () => {
    render(<EmptyState title="No data" />)
    expect(screen.queryByText(/There is no data/i)).not.toBeInTheDocument()
  })

  it('renders icon when provided', () => {
    const icon = <ExclamationTriangleIcon data-testid="icon" />
    render(<EmptyState title="No data" icon={icon} />)
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('renders action button when action is provided', () => {
    const handleClick = jest.fn()
    render(
      <EmptyState
        title="No data"
        action={{ label: 'Create New', onClick: handleClick }}
      />
    )
    
    const button = screen.getByText('Create New')
    expect(button).toBeInTheDocument()
    
    button.click()
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not render action button when action is not provided', () => {
    render(<EmptyState title="No data" />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('merges custom className', () => {
    const { container } = render(<EmptyState title="No data" className="custom-class" />)
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper).toHaveClass('custom-class')
  })
})
