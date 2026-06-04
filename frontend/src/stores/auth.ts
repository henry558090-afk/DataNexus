import { defineStore } from 'pinia'
import { ref } from 'vue'

import http from '@/api/http'

// 登录态：Token + 用户名，持久化到 localStorage
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') ?? '')
  const username = ref<string>(localStorage.getItem('username') ?? '')

  async function login(user: string, password: string): Promise<void> {
    const { data } = await http.post<{ token: string }>('/auth/token/', {
      username: user,
      password,
    })
    token.value = data.token
    username.value = user
    localStorage.setItem('token', data.token)
    localStorage.setItem('username', user)
  }

  function logout(): void {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  return { token, username, login, logout }
})
