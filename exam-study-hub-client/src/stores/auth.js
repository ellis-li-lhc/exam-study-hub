// 鉴权状态：管理 token 与当前用户，处理登录/注册/退出，并联动云端同步。
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { login as apiLogin, register as apiRegister, getMe } from '../api'
import { pullFromCloud, startAutoSync, clearLocalState } from '../sync'

const TOKEN_KEY = 'token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(null)

  const isAuthenticated = computed(() => Boolean(token.value))
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setSession(tokenValue, userValue) {
    token.value = tokenValue
    user.value = userValue
    localStorage.setItem(TOKEN_KEY, tokenValue)
  }

  // 登录成功后的统一收尾：拉云端数据 + 开启自动回写。
  async function afterAuthenticated() {
    await pullFromCloud()
    startAutoSync()
  }

  async function login(payload) {
    const res = await apiLogin(payload)
    // 先清掉本机可能残留的上一个账号的本地状态，避免被当成“待迁移数据”推到本账号云端
    clearLocalState()
    setSession(res.access_token, res.user)
    await afterAuthenticated()
  }

  async function register(payload) {
    const res = await apiRegister(payload)
    clearLocalState()
    setSession(res.access_token, res.user)
    await afterAuthenticated()
  }

  // 应用启动时调用：本地有 token 就校验一次，有效则恢复登录态并开启同步。
  async function restore() {
    if (!token.value) return false
    try {
      user.value = await getMe()
      await afterAuthenticated()
      return true
    } catch {
      // token 失效：清掉，回到未登录。
      logout(false)
      return false
    }
  }

  function logout(clearData = true) {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    if (clearData) clearLocalState()
  }

  return { token, user, isAuthenticated, isAdmin, login, register, restore, logout }
})
