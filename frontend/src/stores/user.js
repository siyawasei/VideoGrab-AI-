import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const membership = computed(() => user.value?.membership || 'free')

  async function login(account, password) {
    const res = await api.login({ account, password })
    token.value = res.data.token
    user.value = res.data.user
    localStorage.setItem('token', res.data.token)
    return res
  }

  async function register(username, email, password) {
    const res = await api.register({ username, email, password })
    token.value = res.data.token
    user.value = res.data.user
    localStorage.setItem('token', res.data.token)
    return res
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await api.getMe()
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  // 初始化时获取用户信息
  if (token.value) {
    fetchUser()
  }

  return { token, user, isLoggedIn, membership, login, register, fetchUser, logout }
})
