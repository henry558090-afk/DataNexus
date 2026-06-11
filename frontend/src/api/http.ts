import axios from 'axios'
import { ElMessage } from 'element-plus'

import router from '@/router'

// 扩展 axios 配置：silent=true 的请求不弹全局错误、不触发 401 跳转（用于登出等丢弃会话场景）
declare module 'axios' {
  interface AxiosRequestConfig {
    silent?: boolean
  }
}

// 统一的 axios 实例：注入 Token、统一错误处理
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '/api',
  timeout: 30000,
})

// 请求拦截：带上 DRF Token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Token ${token}`
  }
  return config
})

// 响应拦截：401 跳登录，其余统一弹错误提示。
// 带 silent 标记的请求（如登出）不弹错误、不触发跳转——它本就要丢弃会话。
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.config?.silent) {
      return Promise.reject(error)
    }
    const status = error.response?.status
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      router.push({ name: 'login' })
    }
    const message =
      error.response?.data?.detail ??
      error.response?.data?.non_field_errors?.[0] ??
      error.message ??
      '请求失败'
    ElMessage.error(String(message))
    return Promise.reject(error)
  },
)

export default http
