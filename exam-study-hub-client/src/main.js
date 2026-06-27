import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './styles/variables.css'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 挂载前先尝试恢复登录态（本地有 token 则校验并拉取云端数据），
// 避免刷新后路由守卫把已登录用户错误地弹回登录页。
const auth = useAuthStore()
auth.restore().finally(() => {
  app.mount('#app')
})
