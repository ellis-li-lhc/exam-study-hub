// 统一的 axios 实例：集中处理 baseURL、token 注入、错误处理。
import axios from 'axios'

const http = axios.create({
  baseURL: '/api',   // 开发期由 Vite 代理转发到后端 8000
  timeout: 10000,
})

// —— 请求拦截器：每个请求自动带上 token（接入登录后生效）——
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// —— 响应拦截器 ——
http.interceptors.response.use(
  // 成功：直接返回响应体 data，业务代码就不用每次写 .data
  (response) => response.data,
  // 失败：统一抛出可读错误（FastAPI 的错误信息在 error.response.data.detail）
  (error) => {
    const status = error.response?.status
    // 401：token 缺失或失效。清掉本地 token，跳回登录页（带上当前路径以便登录后跳回）。
    if (status === 401) {
      localStorage.removeItem('token')
      const path = window.location.pathname + window.location.search
      if (!path.startsWith('/login')) {
        window.location.assign(`/login?redirect=${encodeURIComponent(path)}`)
      }
    }
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export default http
