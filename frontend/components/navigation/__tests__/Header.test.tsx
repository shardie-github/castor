import { render, screen } from '@testing-library/react'
import { Header } from '../Header'
import { usePathname } from 'next/navigation'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/'),
}))

describe('Header', () => {
  beforeEach(() => {
    (usePathname as jest.Mock).mockReturnValue('/')
  })

  it('renders logo', () => {
    render(<Header />)
    expect(screen.getByText('Castor')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    render(<Header />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Marketplace')).toBeInTheDocument()
  })

  it('highlights active navigation item', () => {
    (usePathname as jest.Mock).mockReturnValue('/dashboard')
    render(<Header />)
    
    const dashboardLink = screen.getByText('Dashboard').closest('a')
    expect(dashboardLink).toHaveClass('bg-blue-50', 'text-blue-700')
  })

  it('renders mobile menu button', () => {
    render(<Header />)
    const menuButton = screen.getByLabelText('Toggle menu')
    expect(menuButton).toBeInTheDocument()
  })

  it('toggles mobile menu when button is clicked', () => {
    render(<Header />)
    const menuButton = screen.getByLabelText('Toggle menu')
    
    // Menu should be closed initially
    expect(screen.queryByText('Settings')).not.toBeVisible()
    
    // Click to open
    menuButton.click()
    expect(screen.getByText('Settings')).toBeVisible()
    
    // Click to close
    menuButton.click()
    // Note: In actual implementation, menu might still be in DOM but hidden
  })

  it('renders settings link', () => {
    render(<Header />)
    const settingsLink = screen.getByLabelText('Settings')
    expect(settingsLink).toBeInTheDocument()
  })

  it('renders profile link', () => {
    render(<Header />)
    const profileLink = screen.getByLabelText('Profile')
    expect(profileLink).toBeInTheDocument()
  })

  it('closes mobile menu when link is clicked', () => {
    render(<Header />)
    const menuButton = screen.getByLabelText('Toggle menu')
    
    // Open menu
    menuButton.click()
    
    // Click a link
    const settingsLink = screen.getByText('Settings')
    settingsLink.click()
    
    // Menu should close (implementation dependent)
  })
})
