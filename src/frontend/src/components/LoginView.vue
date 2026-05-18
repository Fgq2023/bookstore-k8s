<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { post, setToken } from '../api/client'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  if (!username.value || !password.value) {
    error.value = 'Username and password are required'
    return
  }
  loading.value = true
  try {
    const res = await post('/auth/login', {
      username: username.value,
      password: password.value
    })
    if (res.success) {
      setToken(res.data.token)
      router.push('/')
    } else {
      error.value = res.error?.message || 'Login failed'
    }
  } catch (e) {
    error.value = e.response?.data?.error?.message || 'Invalid credentials'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-md mx-auto p-6 mt-12">
    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
      <h1 class="text-2xl font-bold text-slate-800 mb-1">Welcome Back</h1>
      <p class="text-slate-500 text-sm mb-6">Sign in to your bookstore account</p>

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
          <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
          <input v-model="password" type="password" placeholder="••••••"
            class="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-base outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all" />
        </div>
      </div>

      <button @click="handleLogin" :disabled="loading"
        class="w-full mt-6 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white py-2.5 rounded-xl font-semibold text-sm transition-colors shadow-sm">
        {{ loading ? 'Signing in...' : 'Sign In' }}
      </button>

      <p class="text-center text-slate-500 text-sm mt-4">
        Don't have an account?
        <router-link to="/register" class="text-blue-600 hover:underline font-medium">Sign up</router-link>
      </p>
    </div>
  </div>
</template>
