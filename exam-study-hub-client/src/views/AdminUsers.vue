<template>
  <div class="admin-page page-stack">
    <section class="page-intro">
      <div>
        <span class="section-kicker">系统管理</span>
        <h2>用户管理</h2>
        <p>查看注册用户、调整角色权限。管理员可访问本页，普通用户不可见。</p>
      </div>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </section>

    <el-card shadow="never" class="users-card">
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column prop="email" label="邮箱" min-width="180">
          <template #default="{ row }">{{ row.email || '—' }}</template>
        </el-table-column>
        <el-table-column label="角色" width="160">
          <template #default="{ row }">
            <el-select
              :model-value="row.role"
              size="small"
              :disabled="row.id === auth.user?.id"
              @change="(role) => changeRole(row, role)"
            >
              <el-option label="普通用户" value="user" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" min-width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" align="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              text
              :disabled="row.id === auth.user?.id"
              @click="removeUser(row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, updateUserRole, deleteUser } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const users = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    users.value = await getUsers()
  } catch (error) {
    ElMessage.error(error.message || '加载用户失败')
  } finally {
    loading.value = false
  }
}

async function changeRole(row, role) {
  if (role === row.role) return
  try {
    const updated = await updateUserRole(row.id, role)
    row.role = updated.role
    ElMessage.success(`已将 ${row.username} 设为${role === 'admin' ? '管理员' : '普通用户'}`)
  } catch (error) {
    ElMessage.error(error.message || '修改角色失败')
  }
}

async function removeUser(row) {
  const confirmed = await ElMessageBox.confirm(
    `确定删除用户「${row.username}」吗？该用户的云端学习数据也会一并删除，且不可恢复。`,
    '删除用户',
    { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
  ).catch(() => false)
  if (!confirmed) return
  try {
    await deleteUser(row.id)
    users.value = users.value.filter(item => item.id !== row.id)
    ElMessage.success('已删除')
  } catch (error) {
    ElMessage.error(error.message || '删除失败')
  }
}

function formatTime(value) {
  if (!value) return '—'
  const d = new Date(value)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(load)
</script>

<style scoped>
.page-stack { display: flex; flex-direction: column; gap: 18px; }
.page-intro { display: flex; align-items: flex-start; justify-content: space-between; }
.page-intro h2 { color: var(--ink); font-size: 1.7rem; }
.page-intro p { margin-top: 5px; color: var(--text-secondary); font-size: .85rem; }
.section-kicker { display: block; margin-bottom: 5px; color: var(--primary); font-size: .72rem; font-weight: 800; letter-spacing: .1em; }
.users-card { border-radius: 18px; border-color: var(--line); }
</style>
