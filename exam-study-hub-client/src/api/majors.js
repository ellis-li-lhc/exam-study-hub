// 专业相关接口
import http from './request'

// 获取专业列表  → GET /api/majors
export function getMajors() {
  return http.get('/majors')
}

// 新建专业  → POST /api/majors
export function createMajor(data) {
  return http.post('/majors', data)
}
