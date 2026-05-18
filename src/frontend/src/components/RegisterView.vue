<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { post, setToken } from '../api/client'

const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''
  if (!username.value || !email.value || !password.value) {
    error.value = 'All fields are required'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  if (password.value.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }
  loading.value = true
  try {
    const res = await post('/auth/register', {
      username: username.value,
      email: email.value,
      password: password.value
    })
    if (res.success) {
      setToken(res.data.token)
      router.push('/')
    } else {
      error.value = res.error?.message || 'Registration failed'
    }
  } catch (e) {
    error.value = e.response?.data?.error?.message || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-md mx-auto p-6 mt-12">
    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
      <h1 class="text-2xl font-bold text-slate-800 mb-1">Create Account</h1>
      <p class="text-slate-500 text-sm mb-6">Join the Cloud-Native Bookstore</p>

      <div v-if="error" class="bg-red-50 text-red-600 text-sm px-4 py-3 rounded-xl mb-4">
        {{ error }}
      </div>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Username</label>
          <input v-model="username" type="text" placeholder="johndoe"
            class="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-base outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Email</label>
          <input v-model="email" type="email" placeholder="john@example.com"
            class="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-base outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
          <input v-model="password" type="password" placeholder="••••••"
            class="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-base outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Confirm Password</label>
          <input v-model="confirmPassword" type="password" placeholder="••••••"
            class="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-base outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all" />
        </div>
      </div>

      <button @click="handleRegister" :disabled="loading"
        class="w-full mt-6 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white py-2.5 rounded-xl font-semibold text-sm transition-colors shadow-sm">
        {{ loading ? 'Creating account...' : 'Sign Up' }}
      </button>

      <p class="text-center text-slate-500 text-sm mt-4">
        Already have an account?
        <router-link to="/login" class="text-blue-600 hover:underline font-medium">Log in</router-link>
      </p>
    </div>
  </div>
</template>
