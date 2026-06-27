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

const mode = ref('login')
const loading = ref(false)
const formRef = ref()
const form = reactive({ username: '', password: '', email: '' })

const rules = {
  username: [{ required: true, min: 2, max: 64, message: '请输入 2-64 个字符的用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }]
}

// 切换登录/注册时清掉上一次的校验提示
watch(mode, () => formRef.value?.clearValidate())

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login({ username: form.username, password: form.password })
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

<style scoped>
.auth-page { min-height: 100vh; display: grid; place-items: center; padding: 24px; background: linear-gradient(145deg, #eaf2ff, #f8fbff 60%); }
.auth-card { width: 100%; max-width: 400px; padding: 32px 30px 36px; background: #fff; border-radius: 20px; border: 1px solid var(--line); box-shadow: 0 18px 48px rgba(37,99,235,.12); }
.auth-brand { display: flex; align-items: center; gap: 12px; }
.brand-mark { width: 44px; height: 44px; display: grid; place-items: center; border-radius: 13px; color: #fff; background: linear-gradient(145deg,var(--primary),#5b8ff9); box-shadow: 0 8px 20px rgba(37,99,235,.25); }
.brand-mark .el-icon { font-size: 23px; }
.auth-brand strong { display: block; color: var(--ink); font-size: 1.1rem; }
.auth-brand small { display: block; color: var(--text-muted); font-size: .76rem; margin-top: 1px; }
.auth-tip { margin: 18px 0 4px; color: var(--text-secondary); font-size: .82rem; line-height: 1.6; }
.auth-tabs { margin-top: 6px; }
.auth-submit { width: 100%; margin-top: 6px; }
</style>
