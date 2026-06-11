import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import http from '@/api/http'

// 当前用户角色（来自后端 /auth/me/）
interface Profile {
  username: string
  is_superuser: boolean
  is_assistant_admin: boolean
  is_boss: boolean
  is_manager: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') ?? '')
  const profile = ref<Profile | null>(null)

  const username = computed(() => profile.value?.username ?? localStorage.getItem('username') ?? '')
  // 是否可进入管理端（超管或辅助管理员）
  const isManager = computed(() => profile.value?.is_manager ?? false)

  async function login(user: string, password: string): Promise<void> {
    const { data } = await http.post<{ token: string }>('/auth/token/', {
      username: user,
      password,
    })
    token.value = data.token
    localStorage.setItem('token', data.token)
    localStorage.setItem('username', user)
    await fetchProfile()
  }

  async function fetchProfile(): Promise<Profile> {
    const { data } = await http.get<Profile>('/auth/me/')
    profile.value = data
    return data
  }

  async function logout(): Promise<void> {
    // 先让服务端 Token 失效（SEC2），失败也继续清本地，保证一定能登出
    try {
      await http.post('/auth/logout/')
    } catch {
      /* 忽略：网络/已过期都不影响本地登出 */
    }
    token.value = ''
    profile.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  return { token, profile, username, isManager, login, fetchProfile, logout }
})
