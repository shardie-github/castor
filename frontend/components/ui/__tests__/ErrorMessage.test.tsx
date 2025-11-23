import { render, screen } from '@testing-library/react'
import { ErrorMessage } from '../ErrorMessage'

describe('ErrorMessage', () => {
  it('renders error message', () => {
    render(<ErrorMessage message="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders default title', () => {
    render(<ErrorMessage message="Error message" />)
    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('renders custom title', () => {
    render(<ErrorMessage title="Custom Error" message="Error message" />)
    expect(screen.getByText('Custom Error')).toBeInTheDocument()
  })

  it('renders retry button when onRetry is provided', () => {
    const handleRetry = jest.fn()
    render(<ErrorMessage message="Error" onRetry={handleRetry} />)
    
    const retryButton = screen.getByText('Try again')
    expect(retryButton).toBeInTheDocument()
    
    retryButton.click()
    expect(handleRetry).toHaveBeenCalledTimes(1)
  })

  it('does not render retry button when onRetry is not provided', () => {
    render(<ErrorMessage message="Error" />)
    expect(screen.queryByText('Try again')).not.toBeInTheDocument()
  })

  it('applies error styling classes', () => {
    const { container } = render(<ErrorMessage message="Error" />)
    const errorDiv = container.firstChild as HTMLElement
    expect(errorDiv).toHaveClass('bg-red-50', 'border-red-200')
  })
})
