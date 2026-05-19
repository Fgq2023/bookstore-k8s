import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import CartView from '../CartView.vue'
import { get, post, put, del } from '../../api/client'
import { store } from '../../store'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush })
}))

vi.mock('../../api/client', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn()
}))

vi.mock('../../store', () => ({
  store: { cartCount: 0 }
}))

describe('CartView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockPush.mockClear()
    store.cartCount = 0
  })

  function mountCart() {
    return mount(CartView, {
      global: {
        stubs: { 'router-link': { template: '<a><slot /></a>' } },
        provide: { toast: vi.fn() }
      }
    })
  }

  it('renders empty cart state', async () => {
    get.mockResolvedValue({ items: [], total: 0 })
    const wrapper = mountCart()
    await flushPromises()
    expect(wrapper.text()).toContain('Your cart is empty')
    expect(wrapper.text()).toContain('Browse Books')
  })

  it('renders cart items and total', async () => {
    get.mockResolvedValue({
      items: [
        { id: 1, title: 'Book A', author: 'Alice', price: 10, quantity: 2 },
        { id: 2, title: 'Book B', author: 'Bob', price: 15, quantity: 1 }
      ],
      total: 35
    })
    const wrapper = mountCart()
    await flushPromises()

    expect(wrapper.text()).toContain('Book A')
    expect(wrapper.text()).toContain('Book B')
    expect(wrapper.text()).toContain('Total: $35.00')
    expect(store.cartCount).toBe(2)
  })

  it('calls remove API when Remove clicked', async () => {
    get.mockResolvedValue({
      items: [{ id: 1, title: 'Book A', author: 'Alice', price: 10, quantity: 1 }],
      total: 10
    })
    del.mockResolvedValue({})
    const toastFn = vi.fn()
    const wrapper = mount(CartView, {
      global: { stubs: ['router-link'], provide: { toast: toastFn } }
    })
    await flushPromises()

    await wrapper.find('button.bg-red-500').trigger('click')
    await flushPromises()

    expect(del).toHaveBeenCalledWith('/cart/item/1')
    expect(toastFn).toHaveBeenCalledWith('Removed from cart')
  })

  it('calls place order API and redirects', async () => {
    get.mockResolvedValue({
      items: [{ id: 1, title: 'Book A', author: 'Alice', price: 10, quantity: 1 }],
      total: 10
    })
    post.mockResolvedValue({ order_id: 42 })
    const toastFn = vi.fn()
    const wrapper = mount(CartView, {
      global: { stubs: ['router-link'], provide: { toast: toastFn } }
    })
    await flushPromises()

    await wrapper.find('button.bg-blue-600').trigger('click')
    await flushPromises()

    expect(post).toHaveBeenCalledWith('/orders')
    expect(toastFn).toHaveBeenCalledWith('Order placed! #42')
    expect(mockPush).toHaveBeenCalledWith('/orders')
  })
})
