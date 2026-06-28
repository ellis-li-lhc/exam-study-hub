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
