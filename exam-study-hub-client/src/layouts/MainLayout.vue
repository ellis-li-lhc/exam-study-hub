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

      <nav class="nav-groups" aria-label="主导航">
        <section v-for="group in menuGroups" :key="group.title" class="nav-group">
          <p class="nav-group-title">{{ group.title }}</p>
          <el-menu :default-active="route.path" router class="nav-menu">
            <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
              <span v-if="item.path === '/diagnosis' && !store.diagnosisComplete" class="nav-dot"></span>
            </el-menu-item>
          </el-menu>
        </section>
      </nav>

      <div class="goal-summary">
        <p class="eyebrow">当前目标</p>
        <template v-if="store.profileComplete">
          <strong>{{ store.selectedMajor?.name }}</strong>
          <span>{{ provinceLabel }}</span>
          <span v-if="store.selectedInstitution">{{ store.selectedInstitution.name }}</span>
          <div class="goal-score">
            <small>目标分</small>
            <b :class="{ pending: !store.diagnosisComplete }">{{ goalScoreText }}</b>
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
          <div class="context-strip">
            <span v-for="chip in contextChips" :key="chip.label" class="context-chip" :class="chip.tone">
              <i class="chip-dot" aria-hidden="true"></i>
              <small>{{ chip.label }}</small>
              <strong>{{ chip.value }}</strong>
            </span>
          </div>
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
      <nav class="nav-groups" aria-label="移动端主导航">
        <section v-for="group in menuGroups" :key="group.title" class="nav-group">
          <p class="nav-group-title">{{ group.title }}</p>
          <el-menu :default-active="route.path" router class="nav-menu" @select="mobileOpen = false">
            <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
              <el-icon><component :is="item.icon" /></el-icon><span>{{ item.title }}</span>
            </el-menu-item>
          </el-menu>
        </section>
      </nav>
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
    await auth.logoutWithFlush()
    router.replace('/login')
  }
}

const menuGroups = computed(() => {
  const groups = [
    {
      title: '报考路径',
      items: [
        { path: '/home', title: '备考总览', icon: 'Grid' },
        { path: '/profile', title: '报考档案', icon: 'User' },
        { path: '/schools', title: '专业与院校', icon: 'School' },
        { path: '/diagnosis', title: '入学诊断', icon: 'DataAnalysis' },
        { path: '/target', title: '目标分分析', icon: 'Aim' }
      ]
    },
    {
      title: '学习执行',
      items: [
        { path: '/plan', title: '学习路线', icon: 'Calendar' },
        { path: '/progress', title: '学习进度', icon: 'TrendCharts' },
        { path: '/english', title: '英语特训', icon: 'Notebook' },
        { path: '/math', title: '数学特训', icon: 'Histogram' },
        { path: '/politics', title: '政治特训', icon: 'Reading' }
      ]
    }
  ]
  if (auth.isAdmin) {
    groups.push({
      title: '系统管理',
      items: [
        { path: '/admin/users', title: '用户管理', icon: 'Setting' },
        { path: '/admin/data', title: '数据管理', icon: 'DataBoard' }
      ]
    })
  }
  return groups
})

const provinceLabel = computed(() => store.selectedProvinces.map(item => item.label).join('、'))
const goalScoreText = computed(() => {
  if (!store.selectedInstitution) return '选择院校后生成'
  return store.diagnosisComplete ? String(store.targetScore) : '诊断后生成'
})
const contextChips = computed(() => [
  { label: '专业', value: store.selectedMajor?.name || '未建档', tone: 'blue' },
  { label: '年度', value: `${store.profile.examYear || '—'} 年`, tone: 'neutral' },
  { label: '目标分', value: store.diagnosisComplete ? String(store.targetScore) : '诊断后生成', tone: 'green' },
  { label: '倒计时', value: `${store.daysUntilExam} 天`, tone: 'amber' }
])
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
    '/english': '基础越弱，越要先过单词关',
    '/math': '公式、思路和例题一起过',
    '/politics': '按考试板块拆清楚再背',
    '/admin/users': '维护账号、角色和用户填报信息',
    '/admin/data': '检查招生数据、专业计划和题库质量'
  }
  return subtitles[route.path] || '个人备考工作台'
})
</script>

<style scoped>
.app-shell { min-height: 100vh; }
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 100;
  width: var(--study-sidebar);
  padding: 20px 14px;
  background: rgba(255, 255, 255, .98);
  border-right: 1px solid var(--line);
  overflow-y: auto;
}
.brand { display: flex; align-items: center; gap: 12px; padding: 0 8px 18px; }
.brand-mark {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: #fff;
  background: var(--primary-deep);
  box-shadow: var(--shadow-xs);
}
.brand-mark .el-icon { font-size: 21px; }
.brand strong,.brand small { display:block; }
.brand strong { color: var(--ink); font-size: 1.02rem; letter-spacing: 0; }
.brand small { color: var(--text-muted); font-size: .73rem; margin-top: 1px; }
.cycle-card {
  margin: 0 4px 16px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--surface-soft);
}
.cycle-top { display:flex; align-items:center; justify-content:space-between; color:var(--ink); font-size:.82rem; font-weight:800; }
.cycle-progress { height:6px; margin:12px 0 8px; border-radius:999px; background:#e1e8f2; overflow:hidden; }
.cycle-progress span { display:block; height:100%; border-radius:inherit; background:var(--primary); transition:width .3s ease; }
.cycle-card small { color:var(--text-muted); font-size:.72rem; }
.nav-groups { display:flex; flex-direction:column; gap:14px; }
.nav-group-title {
  margin: 0 8px 6px;
  color: var(--text-muted);
  font-size: .68rem;
  font-weight: 900;
  letter-spacing: .08em;
}
.nav-menu { border:0; background:transparent; }
.nav-menu .el-menu-item {
  height:42px;
  margin:2px 0;
  border-radius:10px;
  color:var(--text-secondary);
  font-size:.86rem;
}
.nav-menu .el-menu-item:hover { color:var(--primary); background:var(--primary-faint); }
.nav-menu .el-menu-item.is-active {
  color:var(--primary-deep);
  background:var(--primary-soft);
  font-weight:800;
}
.nav-menu .el-menu-item .el-icon { font-size:18px; }
.nav-dot { width:7px; height:7px; margin-left:auto; border-radius:50%; background:var(--accent); }
.goal-summary {
  margin:18px 4px 0;
  padding:16px;
  border: 1px solid rgba(255, 255, 255, .12);
  border-radius: var(--radius-lg);
  color:#dbe7f4;
  background:#111f33;
}
.goal-summary .eyebrow { color:#9fb1c8; }
.goal-summary strong,.goal-summary span { display:block; }
.goal-summary strong { margin:7px 0 3px; color:#fff; line-height:1.35; }
.goal-summary span { color:#c8d6e6; font-size:.76rem; margin-top:3px; }
.goal-score { display:flex; align-items:flex-end; justify-content:space-between; margin-top:14px; padding-top:12px; border-top:1px solid rgba(255,255,255,.14); }
.goal-score small { color:#9fb1c8; }
.goal-score b { color:#fff; font-size:1.45rem; line-height:1; text-align:right; }
.goal-score b.pending { font-size:.82rem; line-height:1.35; max-width:118px; }
.content-shell { margin-left:var(--study-sidebar); min-width:0; }
.topbar {
  min-height:68px;
  padding:8px 26px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:18px;
  position:sticky;
  top:0;
  z-index:80;
  background:rgba(248, 250, 252, .94);
  border-bottom:1px solid rgba(217, 226, 239, .9);
  backdrop-filter:blur(16px);
}
.topbar-title { display:flex; align-items:center; gap:10px; min-width:0; }
.topbar-title h1 { font-size:1.04rem; color:var(--ink); line-height:1.35; }
.eyebrow { color:var(--text-muted); font-size:.7rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
.topbar-actions { display:flex; align-items:center; gap:12px; min-width:0; }
.context-strip {
  min-height:44px;
  display:flex;
  align-items:center;
  gap:0;
  min-width:0;
  padding:4px;
  border:1px solid rgba(210, 221, 236, .92);
  border-radius:14px;
  background:rgba(255, 255, 255, .82);
  box-shadow:0 10px 24px rgba(17, 31, 51, .05);
}
.context-chip {
  min-width:82px;
  max-width:132px;
  min-height:34px;
  display:grid;
  grid-template-columns:auto minmax(0, 1fr);
  grid-template-areas:
    "dot label"
    "dot value";
  column-gap:7px;
  align-items:center;
  padding:5px 11px;
  border:0;
  border-radius:10px;
  background:transparent;
  line-height:1.1;
  transition:background-color .18s ease;
}
.context-chip + .context-chip {
  border-left:1px solid #e4ebf4;
  border-top-left-radius:0;
  border-bottom-left-radius:0;
}
.context-chip:hover { background:#f8fafc; }
.chip-dot {
  grid-area:dot;
  width:7px;
  height:7px;
  border-radius:999px;
  background:#94a3b8;
}
.context-chip small,
.context-chip strong { display:block; white-space:nowrap; }
.context-chip small {
  grid-area:label;
  color:var(--text-muted);
  font-size:.6rem;
  font-weight:800;
}
.context-chip strong {
  grid-area:value;
  margin-top:1px;
  color:var(--ink);
  font-size:.74rem;
  overflow:hidden;
  text-overflow:ellipsis;
}
.context-chip.blue .chip-dot { background:var(--primary); }
.context-chip.green .chip-dot { background:var(--mint); }
.context-chip.amber .chip-dot { background:var(--accent); }
.mobile-menu { display:none; }
.user-trigger {
  min-height:44px;
  display:flex;
  align-items:center;
  gap:8px;
  padding:4px 6px 4px 4px;
  border-radius:999px;
  cursor:pointer;
  outline:none;
  color:var(--text-secondary);
}
.user-trigger:hover { background:#eef3f8; }
.user-trigger .user-name { font-size:.84rem; font-weight:700; color:var(--ink); }
.user-trigger .el-icon { font-size:13px; color:var(--text-muted); }
.main-content { width:100%; max-width:var(--content-max); margin:0 auto; padding:24px 28px 48px; }
.page-enter-active,.page-leave-active { transition:opacity .18s ease,transform .18s ease; }
.page-enter-from { opacity:0; transform:translateY(8px); }
.page-leave-to { opacity:0; transform:translateY(-5px); }
.mobile-brand { padding:22px 14px 12px; }
@media (max-width: 1120px) {
  .context-strip { display:none; }
}
@media (max-width: 900px) {
  .sidebar{display:none}
  .content-shell{margin-left:0}
  .mobile-menu{display:inline-flex}
  .topbar{padding:10px 16px}
  .main-content{padding:20px 16px 40px}
  .user-name{display:none}
}
</style>
