<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <span class="brand-mark"><el-icon><Reading /></el-icon></span>
        <div>
          <strong>上岸计划</strong>
          <small>成人专升本备考</small>
        </div>
      </div>

      <p class="auth-tip">登录后，报考档案、入学诊断与学习进度将同步到云端，换设备也不丢。</p>
      <p class="release-note">河南/江苏公开数据试运行版 · 2025 公开数据 + 2026 备考规划参考 · 不构成录取承诺</p>

      <el-tabs v-model="mode" class="auth-tabs" stretch>
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="2-64 个字符" :prefix-icon="User" />
        </el-form-item>
        <el-form-item v-if="mode === 'register'" label="邮箱（选填）" prop="email">
          <el-input v-model="form.email" placeholder="用于找回密码（可不填）" :prefix-icon="Message" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" :prefix-icon="Lock" @keyup.enter="submit" />
        </el-form-item>
        <div v-if="mode === 'login'" class="auth-options">
          <el-checkbox v-model="rememberPassword">记住密码</el-checkbox>
        </div>
        <el-button type="primary" class="auth-submit" :loading="loading" @click="submit">
          {{ mode === 'login' ? '登录' : '注册并登录' }}
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const DEFAULT_LOGIN = Object.freeze({ username: 'admin', password: '200066' })
const REMEMBERED_LOGIN_KEY = 'exam-study-hub:remembered-login'
const rememberedLogin = readRememberedLogin()

const mode = ref('login')
const loading = ref(false)
const rememberPassword = ref(Boolean(rememberedLogin))
const formRef = ref()
const form = reactive({
  username: rememberedLogin?.username || DEFAULT_LOGIN.username,
  password: rememberedLogin?.password || DEFAULT_LOGIN.password,
  email: ''
})

const rules = {
  username: [{ required: true, min: 2, max: 64, message: '请输入 2-64 个字符的用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }]
}

// 切换登录/注册时清掉上一次的校验提示
watch(mode, () => formRef.value?.clearValidate())

watch(rememberPassword, remember => {
  if (!remember) clearRememberedLogin()
})

function readRememberedLogin() {
  try {
    const raw = localStorage.getItem(REMEMBERED_LOGIN_KEY)
    if (!raw) return null
    const value = JSON.parse(raw)
    if (typeof value?.username !== 'string' || typeof value?.password !== 'string') return null
    return { username: value.username, password: value.password }
  } catch {
    return null
  }
}

function saveRememberedLogin() {
  localStorage.setItem(
    REMEMBERED_LOGIN_KEY,
    JSON.stringify({ username: form.username, password: form.password })
  )
}

function clearRememberedLogin() {
  localStorage.removeItem(REMEMBERED_LOGIN_KEY)
}

function syncRememberPreference() {
  if (rememberPassword.value) {
    saveRememberedLogin()
  } else {
    clearRememberedLogin()
  }
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login({ username: form.username, password: form.password })
      syncRememberPreference()
    } else {
      await auth.register({ username: form.username, password: form.password, email: form.email || undefined })
    }
    ElMessage.success(mode.value === 'login' ? '登录成功' : '注册成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/home'
    router.replace(redirect)
  } catch (error) {
    ElMessage.error(error.message || '操作失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="less" src="../styles/views/Login.less"></style>
