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

// 删除用户  → DELETE /api/admin/users/{id}
export function deleteUser(userId) {
  return http.delete(`/admin/users/${userId}`)
}
