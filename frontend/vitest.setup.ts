/**
 * Vitest setup file for frontend tests.
 *
 * Configures:
 * - jest-dom matchers (toBeInTheDocument, toHaveClass, etc.)
 * - Global test utilities
 * - Mock environment for Next.js
 */

import '@testing-library/jest-dom/vitest'
import { vi, beforeAll, afterAll } from 'vitest'

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    prefetch: vi.fn(),
    pathname: '/dashboard',
    query: {},
  }),
  usePathname: () => '/dashboard',
  useSearchParams: () => new URLSearchParams(),
  redirect: vi.fn(),
}))

// Mock Next.js Image component
vi.mock('next/image', () => ({
  default: (props: Record<string, unknown>) => {
    // eslint-disable-next-line @next/next/no-img-element
    return `<img ${Object.entries(props).map(([k, v]) => `${k}="${v}"`).join(' ')} />`
  },
}))

// Mock Clerk auth
vi.mock('@clerk/nextjs', () => ({
  ClerkProvider: ({ children }: { children: React.ReactNode }) => children,
  useUser: () => ({
    isLoaded: true,
    isSignedIn: true,
    user: {
      id: 'test_user_123',
      primaryEmailAddress: { emailAddress: 'test@example.com' },
      firstName: 'Test',
      lastName: 'User',
    },
  }),
  useAuth: () => ({
    isLoaded: true,
    isSignedIn: true,
    userId: 'test_user_123',
    getToken: vi.fn().mockResolvedValue('mock_jwt_token'),
  }),
  SignedIn: ({ children }: { children: React.ReactNode }) => children,
  SignedOut: () => null,
  auth: vi.fn().mockResolvedValue({ userId: 'test_user_123' }),
}))

// Mock Framer Motion to avoid animation issues in tests
// Mock Framer Motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (target, prop) => {
      return prop // Return the property name as the component string (e.g. motion.div -> 'div')
    }
  }),
  AnimatePresence: ({ children }: { children: React.ReactNode }) => children,
  useMotionValue: () => ({ set: vi.fn(), get: vi.fn() }),
  useTransform: () => ({ set: vi.fn(), get: vi.fn() }),
  useSpring: () => ({ set: vi.fn(), get: vi.fn() }),
  LazyMotion: ({ children }: { children: React.ReactNode }) => children,
  m: new Proxy({}, {
    get: (target, prop) => {
      return prop
    }
  }),
}))

// Mock Capacitor (mobile APIs)
vi.mock('@capacitor/haptics', () => ({
  Haptics: {
    impact: vi.fn(),
    notification: vi.fn(),
    vibrate: vi.fn(),
  },
  ImpactStyle: { Medium: 'MEDIUM', Light: 'LIGHT', Heavy: 'HEAVY' },
}))

// Mock window.matchMedia (required for responsive components)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock IntersectionObserver (used by lazy loading)
class MockIntersectionObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  value: MockIntersectionObserver,
})

// Suppress console noise in tests
const originalError = console.error
const originalWarn = console.warn

beforeAll(() => {
  console.error = (...args: unknown[]) => {
    // Suppress React act() warnings and known noise
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('act(') || args[0].includes('Not implemented'))
    ) {
      return
    }
    originalError.call(console, ...args)
  }
  console.warn = (...args: unknown[]) => {
    if (typeof args[0] === 'string' && args[0].includes('Clerk')) {
      return
    }
    originalWarn.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
  console.warn = originalWarn
})
