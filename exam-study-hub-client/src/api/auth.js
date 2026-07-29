// 鉴权相关接口
import http from './request'

// 注册  → POST /api/auth/register  返回 { access_token, token_type, user }
export function register(data) {
  return http.post('/auth/register', data)
}

// 通过 Turnstile 后发送注册邮箱验证码
export function sendRegistrationCode(data) {
  return http.post('/auth/email-code', data)
}

// 登录  → POST /api/auth/login  返回 { access_token, token_type, user }
export function login(data) {
  return http.post('/auth/login', data)
}

// 用 token 换当前用户信息  → GET /api/auth/me
export function getMe() {
  return http.get('/auth/me')
}
