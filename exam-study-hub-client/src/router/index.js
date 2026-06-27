import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import { useApplicationStore } from '../stores/application'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/home',
    children: [
      { path: 'home', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: '备考总览', icon: 'Grid' } },
      { path: 'profile', name: 'Profile', component: () => import('../views/Selection.vue'), meta: { title: '报考档案', icon: 'User' } },
      { path: 'schools', name: 'Schools', component: () => import('../views/Schools.vue'), meta: { title: '专业与院校', icon: 'School' } },
      { path: 'diagnosis', name: 'Diagnosis', component: () => import('../views/Diagnosis.vue'), meta: { title: '入学诊断', icon: 'DataAnalysis' } },
      { path: 'english', name: 'EnglishDrill', component: () => import('../views/EnglishDrill.vue'), meta: { title: '英语特训', icon: 'Notebook' } },
      { path: 'target', name: 'Target', component: () => import('../views/Target.vue'), meta: { title: '目标分分析', icon: 'Aim' } },
      { path: 'plan', name: 'StudyPlan', component: () => import('../views/StudyPlan.vue'), meta: { title: '学习路线', icon: 'Calendar' } },
      { path: 'progress', name: 'Progress', component: () => import('../views/Progress.vue'), meta: { title: '学习进度', icon: 'TrendCharts' } },
      { path: 'selection', redirect: '/profile' }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

// 流程守卫：按「档案 → 院校 → 诊断」的先后顺序解锁后续步骤，避免跳步进入数据尚未就绪的页面。
const NEED_PROFILE = ['Schools', 'Diagnosis', 'Target', 'StudyPlan', 'Progress']
const NEED_INSTITUTION = ['Diagnosis', 'Target', 'StudyPlan', 'Progress']
const NEED_DIAGNOSIS = ['Target', 'StudyPlan', 'Progress']

router.beforeEach((to) => {
  const auth = useAuthStore()

  // 未登录：除登录页外一律跳登录，并记下原目标用于登录后跳回。
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'Login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : {} }
  }
  // 已登录还想去登录页：直接回首页。
  if (to.name === 'Login' && auth.isAuthenticated) {
    return { name: 'Home' }
  }

  const store = useApplicationStore()
  const name = to.name

  if (NEED_PROFILE.includes(name) && !store.profileComplete) return { name: 'Profile' }
  if (NEED_INSTITUTION.includes(name) && !store.selectedInstitution) return { name: 'Schools' }
  if (NEED_DIAGNOSIS.includes(name) && !store.diagnosisComplete) return { name: 'Diagnosis' }
  return true
})

export default router

