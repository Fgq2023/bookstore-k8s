import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import BookCard from '../BookCard.vue'

describe('BookCard', () => {
  const mockBook = {
    id: 1,
    title: 'Cloud Native Patterns',
    author: 'John Doe',
    isbn: '978-1234567890',
    price: 29.99
  }

  it('renders book title and author', () => {
    const wrapper = mount(BookCard, { props: { book: mockBook } })
    expect(wrapper.text()).toContain('Cloud Native Patterns')
    expect(wrapper.text()).toContain('John Doe')
  })

  it('renders ISBN when available', () => {
    const wrapper = mount(BookCard, { props: { book: mockBook } })
    expect(wrapper.text()).toContain('ISBN: 978-1234567890')
  })

  it('renders dash when ISBN is missing', () => {
    const wrapper = mount(BookCard, { props: { book: { ...mockBook, isbn: null } } })
    expect(wrapper.text()).toContain('ISBN: -')
  })

  it('formats price to 2 decimals', () => {
    const wrapper = mount(BookCard, { props: { book: mockBook } })
    expect(wrapper.text()).toContain('$29.99')
  })

  it('emits add event with book id when button clicked', async () => {
    const wrapper = mount(BookCard, { props: { book: mockBook } })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('add')).toBeTruthy()
    expect(wrapper.emitted('add')[0]).toEqual([1])
  })
})
