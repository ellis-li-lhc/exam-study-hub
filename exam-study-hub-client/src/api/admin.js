// 管理员接口（需管理员权限，token 由请求拦截器自动带上）
import http from './request'

// 用户列表  → GET /api/admin/users
export function getUsers() {
  return http.get('/admin/users')
}

// 修改用户角色  → PATCH /api/admin/users/{id}/role
export function updateUserRole(userId, role) {
  return http.patch(`/admin/users/${userId}/role`, { role })
}

// 重置用户密码  → PATCH /api/admin/users/{id}/password
export function resetUserPassword(userId, password) {
  return http.patch(`/admin/users/${userId}/password`, { password })
}

// 查看用户填报信息（报考档案/诊断/进度）  → GET /api/admin/users/{id}/state
export function getUserState(userId) {
  return http.get(`/admin/users/${userId}/state`)
}

// 删除用户  → DELETE /api/admin/users/{id}
export function deleteUser(userId) {
  return http.delete(`/admin/users/${userId}`)
}

// 数据管理总览  → GET /api/admin/data/summary
export function getAdminDataSummary() {
  return http.get('/admin/data/summary')
}

// 院校数据查看  → GET /api/admin/data/institutions
export function getAdminInstitutions(params = {}) {
  return http.get('/admin/data/institutions', { params })
}

// 当前库中的数据导入批次（按来源/年份/批次聚合） → GET /api/admin/data/batches
export function getAdminImportBatches() {
  return http.get('/admin/data/batches')
}

// 题库质量报告 → GET /api/admin/data/question-quality
export function getAdminQuestionQuality() {
  return http.get('/admin/data/question-quality')
}

// 省份 / 专业主数据维护入口 → GET /api/admin/data/catalog
export function getAdminCatalog() {
  return http.get('/admin/data/catalog')
}
