// 招生院校接口
import http from './request'

// 获取院校列表  → GET /api/institutions?province=&major=
export function getInstitutions(params = {}) {
  return http.get('/institutions', { params })
}
