import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Navbar from '../Navbar.vue'
import { isLoggedIn, clearToken } from '../../api/client'

const mockPush = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({ name: 'books' }),
  useRouter: () => ({ push: mockPush })
}))

vi.mock('../../api/client', () => ({
  isLoggedIn: vi.fn(() => false),
  clearToken: vi.fn()
}))

vi.mock('../../store', () => ({
  store: { cartCount: 0 }
}))

describe('Navbar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockPush.mockClear()
    isLoggedIn.mockReturnValue(false)
  })

  function mountNav() {
    return mount(Navbar, {
      global: {
        stubs: {
          'router-link': { template: '<a><slot /></a>' }
        }
      }
    })
  }

  it('shows Sign In and Sign Up when not logged in', () => {
    const wrapper = mountNav()
    expect(wrapper.text()).toContain('Sign In')
    expect(wrapper.text()).toContain('Sign Up')
    expect(wrapper.text()).not.toContain('Logout')
  })

  it('shows Profile and Logout when logged in', () => {
    isLoggedIn.mockReturnValue(true)
    const wrapper = mountNav()
    expect(wrapper.text()).toContain('Profile')
    expect(wrapper.text()).toContain('Logout')
    expect(wrapper.text()).not.toContain('Sign In')
  })

  it('calls logout and redirects on Logout click', async () => {
    isLoggedIn.mockReturnValue(true)
    const wrapper = mountNav()
    await wrapper.find('button').trigger('click')
    expect(clearToken).toHaveBeenCalled()
    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('renders navigation links', () => {
    const wrapper = mountNav()
    expect(wrapper.text()).toContain('Books')
    expect(wrapper.text()).toContain('Cart')
    expect(wrapper.text()).toContain('Orders')
  })
})
