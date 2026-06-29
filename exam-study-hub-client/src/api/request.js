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
// 后端统一返回信封 {code, message, data}：
// - code === 0 视为成功，返回 data，业务代码直接拿到数据；
// - code !== 0 视为业务失败，抛出 message。
http.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) return body.data
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body   // 兜底：非信封响应（如 204 无内容）
  },
  // 失败：HTTP 4xx/5xx，错误体也是信封 {code, message, data:null}
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
    const data = error.response?.data
    const message = data?.message || data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export default http
