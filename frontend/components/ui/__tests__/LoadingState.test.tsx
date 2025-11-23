import { render, screen } from '@testing-library/react'
import { LoadingState } from '../LoadingState'

describe('LoadingState', () => {
  it('renders default loading message', () => {
    render(<LoadingState />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders custom loading message', () => {
    render(<LoadingState message="Please wait..." />)
    expect(screen.getByText('Please wait...')).toBeInTheDocument()
  })

  it('renders spinner', () => {
    const { container } = render(<LoadingState />)
    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  it('applies fullScreen class when fullScreen is true', () => {
    const { container } = render(<LoadingState fullScreen />)
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper).toHaveClass('min-h-screen')
  })

  it('does not apply fullScreen class when fullScreen is false', () => {
    const { container } = render(<LoadingState fullScreen={false} />)
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper).toHaveClass('py-12')
    expect(wrapper).not.toHaveClass('min-h-screen')
  })

  it('merges custom className', () => {
    const { container } = render(<LoadingState className="custom-class" />)
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper).toHaveClass('custom-class')
  })

  it('does not render message when message is empty string', () => {
    render(<LoadingState message="" />)
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
  })
})
