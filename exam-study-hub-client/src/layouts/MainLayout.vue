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
        <section class="release-notice" aria-label="数据试运行说明">
          <div>
            <strong>河南/江苏公开数据试运行版</strong>
            <span>2025 公开数据 + 2026 备考规划参考</span>
          </div>
          <p>院校/专业/录取以当年考试院和院校招生简章为准，不构成录取承诺。</p>
        </section>
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

<style scoped lang="less" src="../styles/layouts/MainLayout.less"></style>
