// 用户云端状态接口（需登录，token 由请求拦截器自动带上）
import http from './request'

// 拉取云端状态  → GET /api/me/state  返回 { app_state, english_extras, vocab_progress }
export function getState() {
  return http.get('/me/state')
}

// 保存云端状态  → PUT /api/me/state  只传需要更新的字段
export function saveState(data) {
  return http.put('/me/state', data)
}
