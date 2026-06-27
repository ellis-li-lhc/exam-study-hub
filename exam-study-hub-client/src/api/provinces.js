// 报考省份接口
import http from './request'

// 获取省份列表  → GET /api/provinces
export function getProvinces() {
  return http.get('/provinces')
}
