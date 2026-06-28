<template>
  <el-container class="app-shell">
    <el-aside class="sidebar" width="264px">
      <div class="brand">
        <span class="brand-mark"><el-icon><Reading /></el-icon></span>
        <div>
          <strong>上岸计划</strong>
          <small>成人专升本备考</small>
        </div>
      </div>

      <div class="cycle-card">
        <div class="cycle-top">
          <span>{{ store.profile.examYear }} 考试周期</span>
        </div>
        <div class="cycle-progress"><span :style="{ width: `${flowProgress}%` }"></span></div>
        <small>已完成 {{ completedSteps }} / 5 项准备</small>
      </div>

      <el-menu :default-active="route.path" router class="nav-menu">
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
          <span v-if="item.path === '/diagnosis' && !store.diagnosisComplete" class="nav-dot"></span>
        </el-menu-item>
      </el-menu>

      <div class="goal-summary">
        <p class="eyebrow">当前目标</p>
        <template v-if="store.profileComplete">
          <strong>{{ store.selectedMajor?.name }}</strong>
          <span>{{ provinceLabel }}</span>
          <span v-if="store.selectedInstitution">{{ store.selectedInstitution.name }}</span>
          <div class="goal-score">
            <small>目标分</small>
            <b>{{ store.targetScore }}</b>
          </div>
        </template>
        <span v-else>先完成报考档案</span>
      </div>
    </el-aside>

    <el-container class="content-shell">
      <el-header class="topbar">
        <div class="topbar-title">
          <el-button class="mobile-menu" text circle @click="mobileOpen = true"><el-icon><Menu /></el-icon></el-button>
          <div>
            <p class="eyebrow">{{ route.meta.title }}</p>
            <h1>{{ headerSubtitle }}</h1>
          </div>
        </div>
        <div class="topbar-actions">
          <el-dropdown trigger="click" @command="onUserCommand">
            <span class="user-trigger">
              <el-avatar :size="36">{{ avatarText }}</el-avatar>
              <span class="user-name">{{ auth.user?.username || '我' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in"><component :is="Component" /></transition>
        </router-view>
      </el-main>
    </el-container>

    <el-drawer v-model="mobileOpen" direction="ltr" size="82%" :with-header="false" class="mobile-drawer">
      <div class="mobile-brand brand">
        <span class="brand-mark"><el-icon><Reading /></el-icon></span>
        <div><strong>上岸计划</strong><small>成人专升本备考</small></div>
      </div>
      <el-menu :default-active="route.path" router class="nav-menu" @select="mobileOpen = false">
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon><span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-drawer>
  </el-container>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useApplicationStore } from '../stores/application'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const store = useApplicationStore()
const auth = useAuthStore()
const mobileOpen = ref(false)

// 进入主框架（已登录）后加载基础数据；这些接口需要登录态。
onMounted(() => {
  store.loadProvinces()
  store.loadInstitutions()
})

const avatarText = computed(() => (auth.user?.username || '我').slice(0, 1).toUpperCase())

async function onUserCommand(command) {
  if (command !== 'logout') return
  const confirmed = await ElMessageBox.confirm(
    '退出后本机将清除当前学习数据（云端已保存），确定退出吗？',
    '退出登录',
    { confirmButtonText: '退出', cancelButtonText: '取消', type: 'warning' }
  ).catch(() => false)
  if (confirmed) {
    auth.logout()
    router.replace('/login')
  }
}

const menuItems = computed(() => {
  const items = [
    { path: '/home', title: '备考总览', icon: 'Grid' },
    { path: '/profile', title: '报考档案', icon: 'User' },
    { path: '/schools', title: '专业与院校', icon: 'School' },
    { path: '/diagnosis', title: '入学诊断', icon: 'DataAnalysis' },
    { path: '/target', title: '目标分分析', icon: 'Aim' },
    { path: '/plan', title: '学习路线', icon: 'Calendar' },
    { path: '/progress', title: '学习进度', icon: 'TrendCharts' },
    { path: '/english', title: '英语特训', icon: 'Notebook' }
  ]
  if (auth.isAdmin) {
    items.push({ path: '/admin/users', title: '用户管理', icon: 'Setting' })
  }
  return items
})

const provinceLabel = computed(() => store.selectedProvinces.map(item => item.label).join('、'))
const completedSteps = computed(() => [
  store.profileComplete,
  Boolean(store.selectedInstitution),
  store.diagnosisComplete,
  store.diagnosisComplete && Boolean(store.targetScore),
  store.diagnosisComplete && store.overallProgress > 0
].filter(Boolean).length)
const flowProgress = computed(() => completedSteps.value * 20)
const headerSubtitle = computed(() => {
  const subtitles = {
    '/home': '今天也向目标靠近一点',
    '/profile': '先把报名选择和学习方式定下来',
    '/schools': '从专业出发，找到合适的招生院校',
    '/diagnosis': '看清当前水平，计划才不会凭感觉',
    '/target': '用可靠的参考线算出安全目标',
    '/plan': '把总目标拆成能完成的阶段',
    '/progress': '记录执行，也允许计划被现实修正',
    '/english': '基础越弱，越要先过单词关'
  }
  return subtitles[route.path] || '个人备考工作台'
})
</script>

<style scoped>
.app-shell { min-height: 100vh; }
.sidebar { position: fixed; inset: 0 auto 0 0; z-index: 100; padding: 22px 14px; background: rgba(255,255,255,.96); border-right: 1px solid var(--line); overflow-y: auto; }
.brand { display: flex; align-items: center; gap: 12px; padding: 0 8px 22px; }
.brand-mark { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 13px; color: #fff; background: linear-gradient(145deg,var(--primary),#5b8ff9); box-shadow: 0 8px 20px rgba(37,99,235,.25); }
.brand-mark .el-icon { font-size: 22px; }
.brand strong,.brand small { display:block; }
.brand strong { color: var(--ink); font-size: 1.05rem; }
.brand small { color: var(--text-muted); font-size: .75rem; margin-top: 1px; }
.cycle-card { margin: 0 4px 18px; padding: 14px; border-radius: 14px; background: #f4f7fb; border: 1px solid #e6edf7; }
.cycle-top { display:flex; align-items:center; justify-content:space-between; color:var(--ink); font-size:.82rem; font-weight:700; }
.cycle-progress { height:5px; margin:12px 0 8px; border-radius:10px; background:#dfe8f5; overflow:hidden; }
.cycle-progress span { display:block; height:100%; border-radius:inherit; background:linear-gradient(90deg,var(--primary),#62a2ff); transition:width .3s ease; }
.cycle-card small { color:var(--text-muted); font-size:.72rem; }
.nav-menu { border:0; background:transparent; }
.nav-menu .el-menu-item { height:46px; margin:3px 0; border-radius:12px; color:var(--text-secondary); }
.nav-menu .el-menu-item:hover { background:var(--primary-soft); }
.nav-menu .el-menu-item.is-active { color:var(--primary-deep); background:#eaf2ff; font-weight:700; }
.nav-dot { width:7px; height:7px; margin-left:auto; border-radius:50%; background:var(--accent); }
.goal-summary { margin:22px 4px 0; padding:16px; border-radius:16px; color:var(--text-secondary); background:linear-gradient(145deg,#14213d,#243b66); }
.goal-summary .eyebrow { color:#9fb5d7; }
.goal-summary strong,.goal-summary span { display:block; }
.goal-summary strong { margin:7px 0 3px; color:#fff; }
.goal-summary span { color:#c9d6ea; font-size:.78rem; margin-top:3px; }
.goal-score { display:flex; align-items:flex-end; justify-content:space-between; margin-top:14px; padding-top:12px; border-top:1px solid rgba(255,255,255,.14); }
.goal-score small { color:#9fb5d7; }.goal-score b { color:#fff; font-size:1.45rem; line-height:1; }
.content-shell { margin-left:264px; min-width:0; }
.topbar { height:76px; padding:0 30px; display:flex; align-items:center; justify-content:space-between; position:sticky; top:0; z-index:80; background:rgba(248,251,255,.88); border-bottom:1px solid rgba(216,225,239,.8); backdrop-filter:blur(16px); }
.topbar-title { display:flex; align-items:center; gap:10px; }.topbar-title h1 { font-size:1.05rem; color:var(--ink); line-height:1.35; }.eyebrow { color:var(--text-muted); font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
.topbar-actions { display:flex; align-items:center; gap:12px; }.mobile-menu { display:none; }
.user-trigger { display:flex; align-items:center; gap:8px; cursor:pointer; outline:none; color:var(--text-secondary); }
.user-trigger .user-name { font-size:.85rem; font-weight:600; color:var(--ink); }
.user-trigger .el-icon { font-size:13px; color:var(--text-muted); }
.main-content { width:100%; max-width:1480px; margin:0 auto; padding:26px 30px 48px; }
.page-enter-active,.page-leave-active { transition:opacity .18s ease,transform .18s ease; }.page-enter-from { opacity:0; transform:translateY(8px); }.page-leave-to { opacity:0; transform:translateY(-5px); }
.mobile-brand { padding:22px 14px; }
@media (max-width: 900px) { .sidebar{display:none}.content-shell{margin-left:0}.mobile-menu{display:inline-flex}.topbar{padding:0 18px}.main-content{padding:20px 16px 40px}.topbar-actions .el-tag{display:none} }
</style>
