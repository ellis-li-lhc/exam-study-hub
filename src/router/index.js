import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/home',
    children: [
      { path: 'home', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: '备考总览', icon: 'Grid' } },
      { path: 'profile', name: 'Profile', component: () => import('../views/Selection.vue'), meta: { title: '报考档案', icon: 'User' } },
      { path: 'schools', name: 'Schools', component: () => import('../views/Schools.vue'), meta: { title: '专业与院校', icon: 'School' } },
      { path: 'diagnosis', name: 'Diagnosis', component: () => import('../views/Diagnosis.vue'), meta: { title: '入学诊断', icon: 'DataAnalysis' } },
      { path: 'target', name: 'Target', component: () => import('../views/Target.vue'), meta: { title: '目标分分析', icon: 'Aim' } },
      { path: 'plan', name: 'StudyPlan', component: () => import('../views/StudyPlan.vue'), meta: { title: '学习路线', icon: 'Calendar' } },
      { path: 'progress', name: 'Progress', component: () => import('../views/Progress.vue'), meta: { title: '学习进度', icon: 'TrendCharts' } },
      { path: 'selection', redirect: '/profile' }
    ]
  }
]

export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

