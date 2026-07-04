<template>
  <div class="admin-page page-stack">
    <section class="page-intro">
      <div>
        <span class="section-kicker">系统管理</span>
        <h2>用户管理</h2>
        <p>查看注册用户与其填报信息、调整角色、重置密码。管理员可访问本页，普通用户不可见。</p>
      </div>
      <el-button class="refresh-btn" :loading="loading" @click="load">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </section>

    <el-card shadow="never" class="users-card">
      <el-table :data="users" v-loading="loading" stripe class="users-table">
        <el-table-column prop="id" label="ID" width="64" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="170">
          <template #default="{ row }">{{ row.email || '—' }}</template>
        </el-table-column>
        <el-table-column label="角色" width="140">
          <template #default="{ row }">
            <el-select
              :model-value="row.role"
              size="small"
              filterable
              :disabled="row.id === auth.user?.id"
              @change="(role) => changeRole(row, role)"
            >
              <el-option label="普通用户" value="user" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" min-width="150">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="148" align="right" header-align="right" class-name="actions-column">
          <template #default="{ row }">
            <div class="row-actions" aria-label="用户操作">
              <el-tooltip content="查看填报" placement="top" :show-after="250">
                <el-button
                  class="action-icon primary"
                  circle
                  aria-label="查看填报"
                  @click="openState(row)"
                >
                  <el-icon><View /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="重置密码" placement="top" :show-after="250">
                <el-button
                  class="action-icon"
                  circle
                  aria-label="重置密码"
                  @click="resetPwd(row)"
                >
                  <el-icon><Key /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="row.id === auth.user?.id ? '不能删除当前账号' : '删除用户'" placement="top" :show-after="250">
                <el-button
                  class="action-icon danger"
                  circle
                  aria-label="删除用户"
                  :disabled="row.id === auth.user?.id"
                  @click="removeUser(row)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="drawerVisible" :title="`${currentUser?.username || ''} 的填报信息`" size="440px">
      <div v-loading="stateLoading" class="state-detail">
        <template v-if="profile">
          <h4 class="block-title">报考档案</h4>
          <dl class="info-list">
            <div><dt>云端版本</dt><dd>v{{ currentState?.sync_version ?? 0 }}<span v-if="currentState?.updated_at"> · {{ formatTime(currentState.updated_at) }}</span></dd></div>
            <div><dt>报考省份</dt><dd>{{ provinceLabels || '—' }}</dd></div>
            <div><dt>意向城市</dt><dd>{{ cityLabels || '不限' }}</dd></div>
            <div><dt>报考专业</dt><dd>{{ majorLabel || '—' }}</dd></div>
            <div><dt>报考科类</dt><dd>{{ majorCategory || '—' }}</dd></div>
            <div><dt>参考年度</dt><dd>{{ profile.examYear || '—' }} 年</dd></div>
            <div><dt>学习模式</dt><dd>{{ profile.mode === 'plan' ? '计划模式' : profile.mode === 'self' ? '自主模式' : '—' }}</dd></div>
            <div v-if="profile.mode === 'plan'"><dt>学习时间</dt><dd>工作日 {{ profile.weekdayHours }} 小时 / 周末 {{ profile.weekendHours }} 小时</dd></div>
            <div><dt>开始日期</dt><dd>{{ profile.startDate || '—' }}</dd></div>
          </dl>

          <h4 class="block-title">入学诊断</h4>
          <dl class="info-list">
            <div><dt>诊断状态</dt><dd>{{ diagnostic?.completed ? '已完成' : '未完成' }}</dd></div>
            <template v-if="diagnostic?.completed">
              <div><dt>预估总分</dt><dd>{{ diagnosticTotal }} / 450</dd></div>
              <div><dt>答对题数</dt><dd>{{ diagnostic.correctCount ?? 0 }} / {{ diagnostic.totalQuestions ?? 0 }}</dd></div>
              <div><dt>整体掌握度</dt><dd>{{ diagnostic.knowledge ?? 0 }}%</dd></div>
            </template>
          </dl>
        </template>
        <el-empty v-else-if="!stateLoading" description="该用户还没有填报任何信息" :image-size="72" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Key, Refresh, View } from '@element-plus/icons-vue'
import { getUsers, updateUserRole, deleteUser, resetUserPassword, getUserState } from '../api'
import { useAuthStore } from '../stores/auth'
import { chinaProvinces } from '../data/regions'
import { examMajors } from '../data/majors'

const auth = useAuthStore()
const users = ref([])
const loading = ref(false)

const drawerVisible = ref(false)
const stateLoading = ref(false)
const currentUser = ref(null)
const currentState = ref(null)

const provinceMap = Object.fromEntries(chinaProvinces.map(p => [p.value, p.label]))
const majorMap = Object.fromEntries(examMajors.map(m => [m.code, m]))

const profile = computed(() => currentState.value?.app_state?.profile || null)
const diagnostic = computed(() => currentState.value?.app_state?.diagnostic || null)
const provinceLabels = computed(() => (profile.value?.provinces || []).map(code => provinceMap[code] || code).join('、'))
const cityLabels = computed(() => (profile.value?.cities || []).join('、'))
const majorLabel = computed(() => majorMap[profile.value?.majorCode]?.name || profile.value?.majorCode || '')
const majorCategory = computed(() => majorMap[profile.value?.majorCode]?.category || '')
const diagnosticTotal = computed(() => {
  const scores = diagnostic.value?.subjectScores || {}
  return Object.values(scores).reduce((sum, v) => sum + Number(v || 0), 0)
})

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

async function openState(row) {
  currentUser.value = row
  currentState.value = null
  drawerVisible.value = true
  stateLoading.value = true
  try {
    currentState.value = await getUserState(row.id)
  } catch (error) {
    ElMessage.error(error.message || '加载填报信息失败')
  } finally {
    stateLoading.value = false
  }
}

async function resetPwd(row) {
  try {
    const { value } = await ElMessageBox.prompt(
      `为「${row.username}」设置新密码（至少 6 位）。出于安全，系统不保存也无法查看明文密码。`,
      '重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputType: 'password',
        inputPattern: /.{6,}/,
        inputErrorMessage: '密码至少 6 位'
      }
    )
    await resetUserPassword(row.id, value)
    ElMessage.success(`已重置 ${row.username} 的密码`)
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(error.message || '重置密码失败')
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
.refresh-btn { min-width: 84px; }
.users-card {
  border-radius: var(--radius-lg);
  border-color: var(--line);
  overflow: hidden;
}
.users-card :deep(.el-card__body) {
  padding: 18px 20px 8px;
  overflow-x: auto;
}
.users-table { min-width: 760px; }
.users-table :deep(.el-table__header th) {
  height: 44px;
  background: #f8fafc;
  color: var(--text-secondary);
  font-weight: 800;
}
.users-table :deep(.el-table__row td) { height: 72px; }
.users-table :deep(.actions-column) { background-image: linear-gradient(90deg, rgba(255,255,255,0), #fff 18px); }
.row-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  min-width: 116px;
}
.row-actions :deep(.el-button + .el-button) { margin-left: 0; }
.action-icon {
  width: 34px;
  height: 34px;
  border: 1px solid transparent;
  color: var(--text-secondary);
  background: transparent;
  transition: background-color .18s ease, border-color .18s ease, color .18s ease, transform .18s ease;
}
.action-icon:hover,
.action-icon:focus-visible {
  border-color: #d7e1ee;
  color: var(--ink);
  background: #f7f9fc;
}
.action-icon:active { transform: scale(.96); }
.action-icon.primary {
  color: var(--primary);
  background: var(--primary-faint);
}
.action-icon.primary:hover,
.action-icon.primary:focus-visible {
  border-color: #bfd1f0;
  color: var(--primary-deep);
  background: var(--primary-soft);
}
.action-icon.danger { color: #dc2626; }
.action-icon.danger:hover,
.action-icon.danger:focus-visible {
  border-color: #fecaca;
  color: #b91c1c;
  background: #fff1f2;
}
.action-icon.is-disabled,
.action-icon.is-disabled:hover {
  border-color: transparent;
  color: #cbd5e1;
  background: transparent;
  transform: none;
}
.state-detail { min-height: 200px; }
.block-title { margin: 6px 0 10px; color: var(--ink); font-size: .92rem; }
.info-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 22px; }
.info-list > div { display: grid; grid-template-columns: 84px 1fr; gap: 10px; align-items: start; }
.info-list dt { color: var(--text-muted); font-size: .8rem; }
.info-list dd { color: var(--ink); font-size: .82rem; line-height: 1.5; }
@media (max-width: 720px) {
  .page-intro { flex-direction: column; gap: 12px; }
  .refresh-btn { align-self: flex-start; }
}
</style>
