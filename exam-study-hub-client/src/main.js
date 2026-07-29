import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/loading/style/css'
import {
  Aim,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Calendar,
  Check,
  CircleCheck,
  Close,
  Compass,
  DataAnalysis,
  DataBoard,
  Delete,
  Edit,
  EditPen,
  Flag,
  Grid,
  Histogram,
  Key,
  Location,
  MagicStick,
  Medal,
  Menu,
  Notebook,
  Reading,
  Refresh,
  School,
  Search,
  Setting,
  SwitchButton,
  Tickets,
  TrendCharts,
  User,
  VideoPlay,
  View,
  Warning,
} from '@element-plus/icons-vue'
import App from './App.vue'
import router, { preloadCommonRoutes } from './router'
import './styles/variables.css'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

const elementIcons = {
  Aim,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Calendar,
  Check,
  CircleCheck,
  Close,
  Compass,
  DataAnalysis,
  DataBoard,
  Delete,
  Edit,
  EditPen,
  Flag,
  Grid,
  Histogram,
  Key,
  Location,
  MagicStick,
  Medal,
  Menu,
  Notebook,
  Reading,
  Refresh,
  School,
  Search,
  Setting,
  SwitchButton,
  Tickets,
  TrendCharts,
  User,
  VideoPlay,
  View,
  Warning,
}

for (const [key, component] of Object.entries(elementIcons)) {
  app.component(key, component)
}

app.use(createPinia())

// 挂载前先尝试恢复登录态（本地有 token 则校验并拉取云端数据），
// 再安装路由，避免刷新直达管理员页面时守卫先于用户信息恢复而误判权限。
const auth = useAuthStore()
auth.restore().finally(() => {
  app.use(router)
  app.mount('#app')

  const preload = () => preloadCommonRoutes()
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(preload, { timeout: 2500 })
  } else {
    window.setTimeout(preload, 500)
  }
})
