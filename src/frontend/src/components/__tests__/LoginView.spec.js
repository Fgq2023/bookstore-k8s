import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginView from '../LoginView.vue'
import { post, setToken } from '../../api/client'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush })
}))

vi.mock('../../api/client', () => ({
  post: vi.fn(),
  setToken: vi.fn()
}))

describe('LoginView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockPush.mockClear()
  })

  it('renders login form elements', () => {
    const wrapper = mount(LoginView)
    expect(wrapper.text()).toContain('Welcome Back')
    expect(wrapper.find('input[type="text"]').exists()).toBe(true)
    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    expect(wrapper.find('button').text()).toContain('Sign In')
  })

  it('shows validation error when fields are empty', async () => {
    const wrapper = mount(LoginView)
    await wrapper.find('button').trigger('click')
    expect(wrapper.text()).toContain('Username and password are required')
  })

  it('calls API and redirects on successful login', async () => {
    post.mockResolvedValue({ success: true, data: { token: 'abc123' } })
    const wrapper = mount(LoginView)

    await wrapper.find('input[type="text"]').setValue('alice')
    await wrapper.find('input[type="password"]').setValue('secret')
    await wrapper.find('button').trigger('click')
    await new Promise(r => setTimeout(r, 0))

    expect(post).toHaveBeenCalledWith('/auth/login', {
      username: 'alice',
      password: 'secret'
    })
    expect(setToken).toHaveBeenCalledWith('abc123')
    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('displays error message on login failure', async () => {
    post.mockResolvedValue({ success: false, error: { message: 'Bad creds' } })
    const wrapper = mount(LoginView)

    await wrapper.find('input[type="text"]').setValue('bob')
    await wrapper.find('input[type="password"]').setValue('wrong')
    await wrapper.find('button').trigger('click')
    await new Promise(r => setTimeout(r, 0))

    expect(wrapper.text()).toContain('Bad creds')
  })

  it('disables button while loading', async () => {
    post.mockImplementation(() => new Promise(() => {}))
    const wrapper = mount(LoginView)

    await wrapper.find('input[type="text"]').setValue('alice')
    await wrapper.find('input[type="password"]').setValue('secret')
    await wrapper.find('button').trigger('click')

    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Signing in...')
  })
})
