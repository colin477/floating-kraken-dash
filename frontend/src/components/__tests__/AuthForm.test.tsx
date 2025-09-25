import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AuthForm } from '../AuthForm'
import { mockApiCall, resetAllMocks } from '../../test/utils'

describe('AuthForm', () => {
  beforeEach(() => {
    resetAllMocks()
  })

  describe('Login Mode', () => {
    it('renders login form correctly', () => {
      render(<AuthForm mode="login" onSuccess={() => {}} />)
      
      expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument()
    })

    it('validates required fields', async () => {
      render(<AuthForm mode="login" onSuccess={() => {}} />)
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
        expect(screen.getByText(/password is required/i)).toBeInTheDocument()
      })
    })

    it('validates email format', async () => {
      render(<AuthForm mode="login" onSuccess={() => {}} />)
      
      const emailInput = screen.getByLabelText(/email/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/invalid email format/i)).toBeInTheDocument()
      })
    })

    it('submits login form successfully', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        refresh_token: 'mock-refresh',
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          id: 'user-id',
          email: 'test@example.com',
          full_name: 'Test User'
        }
      }
      
      mockApiCall('/auth/login', mockResponse)
      const onSuccess = vi.fn()
      
      render(<AuthForm mode="login" onSuccess={onSuccess} />)
      
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith(mockResponse)
      })
    })

    it('handles login error', async () => {
      mockApiCall('/auth/login', { detail: 'Invalid credentials' }, 401)
      
      render(<AuthForm mode="login" onSuccess={() => {}} />)
      
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
      })
    })
  })

  describe('Register Mode', () => {
    it('renders register form correctly', () => {
      render(<AuthForm mode="register" onSuccess={() => {}} />)
      
      expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
      expect(screen.getByText(/already have an account/i)).toBeInTheDocument()
    })

    it('validates password strength', async () => {
      render(<AuthForm mode="register" onSuccess={() => {}} />)
      
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /create account/i })
      
      fireEvent.change(passwordInput, { target: { value: 'weak' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument()
      })
    })

    it('submits register form successfully', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        refresh_token: 'mock-refresh',
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          id: 'user-id',
          email: 'test@example.com',
          full_name: 'Test User'
        }
      }
      
      mockApiCall('/auth/register', mockResponse)
      const onSuccess = vi.fn()
      
      render(<AuthForm mode="register" onSuccess={onSuccess} />)
      
      const nameInput = screen.getByLabelText(/full name/i)
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /create account/i })
      
      fireEvent.change(nameInput, { target: { value: 'Test User' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'Password123!' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith(mockResponse)
      })
    })

    it('handles registration error for existing email', async () => {
      mockApiCall('/auth/register', { detail: 'Email already registered' }, 400)
      
      render(<AuthForm mode="register" onSuccess={() => {}} />)
      
      const nameInput = screen.getByLabelText(/full name/i)
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /create account/i })
      
      fireEvent.change(nameInput, { target: { value: 'Test User' } })
      fireEvent.change(emailInput, { target: { value: 'existing@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'Password123!' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/email already registered/i)).toBeInTheDocument()
      })
    })
  })

  describe('Mode Switching', () => {
    it('switches from login to register mode', () => {
      render(<AuthForm mode="login" onSuccess={() => {}} />)
      
      const switchLink = screen.getByText(/sign up/i)
      fireEvent.click(switchLink)
      
      expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument()
    })

    it('switches from register to login mode', () => {
      render(<AuthForm mode="register" onSuccess={() => {}} />)
      
      const switchLink = screen.getByText(/sign in/i)
      fireEvent.click(switchLink)
      
      expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
    })
  })

  describe('Loading States', () => {
    it('shows loading state during form submission', async () => {
      // Mock a delayed response
      global.fetch = vi.fn().mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ access_token: 'token' })
        }), 100))
      )
      
      render(<AuthForm mode="login" onSuccess={() => {}} />)
      
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)
      
      expect(screen.getByText(/signing in/i)).toBeInTheDocument()
      expect(submitButton).toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('has proper form labels and ARIA attributes', () => {
      render(<AuthForm mode="login" onSuccess={() => {}} />)
      
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      
      expect(emailInput).toHaveAttribute('type', 'email')
      expect(emailInput).toHaveAttribute('required')
      expect(passwordInput).toHaveAttribute('type', 'password')
      expect(passwordInput).toHaveAttribute('required')
    })

    it('announces form errors to screen readers', async () => {
      render(<AuthForm mode="login" onSuccess={() => {}} />)
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        const errorMessage = screen.getByText(/email is required/i)
        expect(errorMessage).toHaveAttribute('role', 'alert')
      })
    })
  })
})