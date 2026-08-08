<template>
  <div class="auth-page">
    <span class="auth-orb auth-orb-one" aria-hidden="true"></span>
    <span class="auth-orb auth-orb-two" aria-hidden="true"></span>

    <main class="auth-shell">
      <section class="auth-story" aria-labelledby="auth-story-title">
        <div class="auth-brand auth-brand-light">
          <span class="brand-mark"><el-icon><Reading /></el-icon></span>
          <div>
            <strong>上岸计划</strong>
            <small>成人专升本备考工作台</small>
          </div>
        </div>

        <div class="story-copy">
          <span class="story-kicker">2026 备考季 · 从现在开始</span>
          <h1 id="auth-story-title">把“想上岸”，<br />变成每天看得见的进度。</h1>
          <p>从报考选择、入学诊断到每日学习计划，把复杂的备考过程拆成下一步就能完成的小目标。</p>
        </div>

        <div class="journey-preview" aria-label="备考路径">
          <div class="journey-heading">
            <div>
              <span>你的备考闭环</span>
              <strong>每一步都有清晰去处</strong>
            </div>
            <span class="journey-badge"><el-icon><TrendCharts /></el-icon> 稳步推进</span>
          </div>
          <ol class="journey-steps">
            <li>
              <span class="step-icon"><el-icon><DocumentChecked /></el-icon></span>
              <div><strong>建立报考档案</strong><small>确认省份、专业与学习方式</small></div>
            </li>
            <li>
              <span class="step-icon"><el-icon><DataAnalysis /></el-icon></span>
              <div><strong>完成入学诊断</strong><small>看清基础，找到优先提分项</small></div>
            </li>
            <li>
              <span class="step-icon"><el-icon><Calendar /></el-icon></span>
              <div><strong>执行学习计划</strong><small>按阶段推进，随进度及时纠偏</small></div>
            </li>
          </ol>
        </div>

        <div class="story-footer">
          <span><el-icon><CircleCheck /></el-icon> 学习进度云端同步</span>
          <span><el-icon><CircleCheck /></el-icon> 河南 / 江苏公开数据试运行</span>
        </div>
      </section>

      <section class="auth-panel" aria-labelledby="auth-form-title">
        <div class="auth-brand auth-brand-mobile">
          <span class="brand-mark"><el-icon><Reading /></el-icon></span>
          <div><strong>上岸计划</strong><small>成人专升本备考工作台</small></div>
        </div>

        <div class="auth-panel-inner">
          <div class="auth-heading">
            <span class="auth-eyebrow">{{ mode === 'login' ? 'WELCOME BACK' : 'CREATE ACCOUNT' }}</span>
            <h2 id="auth-form-title">{{ mode === 'login' ? '欢迎回来' : '创建你的备考档案' }}</h2>
            <p>{{ mode === 'login' ? '登录后继续上次的学习进度。' : '注册后即可开始报考规划与入学诊断。' }}</p>
          </div>

          <el-tabs v-model="mode" class="auth-tabs" stretch>
            <el-tab-pane label="账号登录" name="login" />
            <el-tab-pane label="新用户注册" name="register" />
          </el-tabs>

          <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" size="large" autocomplete="username" placeholder="请输入用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item v-if="mode === 'register'" label="邮箱" prop="email">
              <el-input v-model="form.email" size="large" type="email" autocomplete="email" placeholder="用于验证身份与找回密码" :prefix-icon="Message" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                size="large"
                type="password"
                show-password
                :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
                placeholder="至少 6 位字符"
                :prefix-icon="Lock"
                @keyup.enter="submit"
              />
            </el-form-item>
            <template v-if="mode === 'register'">
              <el-form-item label="安全验证" class="turnstile-form-item">
                <TurnstileWidget
                  ref="turnstileRef"
                  :site-key="turnstileSiteKey"
                  action="register"
                  @verified="handleTurnstileVerified"
                  @expired="turnstileToken = ''"
                  @error="handleTurnstileError"
                />
              </el-form-item>
              <el-form-item label="邮箱验证码" prop="verificationCode">
                <div class="verification-code-row">
                  <el-input
                    v-model="form.verificationCode"
                    size="large"
                    inputmode="numeric"
                    autocomplete="one-time-code"
                    maxlength="6"
                    placeholder="6 位数字"
                    :prefix-icon="Key"
                    @input="form.verificationCode = form.verificationCode.replace(/\D/g, '').slice(0, 6)"
                    @keyup.enter="submit"
                  />
                  <el-button
                    class="send-code-button"
                    native-type="button"
                    :loading="sendingCode"
                    :disabled="countdown > 0 || !turnstileSiteKey"
                    @click="sendCode"
                  >
                    {{ countdown > 0 ? `${countdown}s 后重发` : '获取验证码' }}
                  </el-button>
                </div>
                <p class="verification-delivery-tip">
                  <el-icon><InfoFilled /></el-icon>
                  验证码邮件可能被归入垃圾邮件或广告邮件，请留意并将发件人加入白名单。
                </p>
                <p v-if="codeSentForCurrentEmail" class="verification-hint" aria-live="polite">
                  <el-icon><CircleCheck /></el-icon>
                  验证码已发送，10 分钟内有效，请同时检查垃圾邮箱。
                </p>
              </el-form-item>
            </template>
            <div v-if="mode === 'login'" class="auth-options">
              <el-checkbox v-model="rememberUsername">记住密码</el-checkbox>
              <el-button link type="primary" class="forgot-password-link" @click="openForgotPassword">忘记密码？</el-button>
            </div>
            <p v-else class="register-tip"><el-icon><CircleCheck /></el-icon> 注册即创建独立学习空间，进度可跨设备同步。</p>
            <el-button type="primary" size="large" native-type="submit" class="auth-submit" :loading="loading" @click="submit">
              {{ mode === 'login' ? '进入备考工作台' : '注册并开始规划' }}
              <el-icon v-if="!loading" class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </el-form>

          <el-dialog
            v-model="forgotOpen"
            title="找回密码"
            width="min(520px, calc(100vw - 32px))"
            :close-on-click-modal="false"
            destroy-on-close
            class="password-reset-dialog"
          >
            <p class="password-reset-intro">输入注册邮箱，验证身份后即可设置新的登录密码。</p>
            <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-position="top" @submit.prevent>
              <el-form-item label="注册邮箱" prop="email">
                <el-input v-model="resetForm.email" size="large" type="email" autocomplete="email" placeholder="请输入注册时使用的邮箱" :prefix-icon="Message" />
              </el-form-item>
              <el-form-item label="安全验证" class="turnstile-form-item">
                <TurnstileWidget
                  ref="resetTurnstileRef"
                  :site-key="turnstileSiteKey"
                  action="password-reset"
                  @verified="handleResetTurnstileVerified"
                  @expired="resetTurnstileToken = ''"
                  @error="handleResetTurnstileError"
                />
              </el-form-item>
              <el-form-item label="邮箱验证码" prop="verificationCode">
                <div class="verification-code-row">
                  <el-input
                    v-model="resetForm.verificationCode"
                    size="large"
                    inputmode="numeric"
                    autocomplete="one-time-code"
                    maxlength="6"
                    placeholder="6 位数字"
                    :prefix-icon="Key"
                    @input="resetForm.verificationCode = resetForm.verificationCode.replace(/\D/g, '').slice(0, 6)"
                  />
                  <el-button
                    class="send-code-button"
                    native-type="button"
                    :loading="sendingResetCode"
                    :disabled="resetCountdown > 0 || !turnstileSiteKey"
                    @click="sendResetCode"
                  >
                    {{ resetCountdown > 0 ? `${resetCountdown}s 后重发` : '获取验证码' }}
                  </el-button>
                </div>
                <p class="verification-delivery-tip"><el-icon><InfoFilled /></el-icon>验证码邮件可能被归入垃圾邮件或广告邮件，请留意并将发件人加入白名单。</p>
                <p v-if="resetCodeSentForCurrentEmail" class="verification-hint" aria-live="polite"><el-icon><CircleCheck /></el-icon>如果该邮箱已注册，验证码已发送，10 分钟内有效。</p>
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input v-model="resetForm.newPassword" size="large" type="password" show-password autocomplete="new-password" placeholder="至少 6 位字符" :prefix-icon="Lock" />
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirmPassword">
                <el-input v-model="resetForm.confirmPassword" size="large" type="password" show-password autocomplete="new-password" placeholder="请再次输入新密码" :prefix-icon="Lock" @keyup.enter="submitPasswordReset" />
              </el-form-item>
            </el-form>
            <template #footer>
              <el-button @click="forgotOpen = false">取消</el-button>
              <el-button type="primary" :loading="resetLoading" @click="submitPasswordReset">确认重置密码</el-button>
            </template>
          </el-dialog>

          <div class="release-note">
            <el-icon><InfoFilled /></el-icon>
            <p><strong>公开数据试运行版</strong><span>2025 公开数据 + 2026 备考规划参考，院校与录取信息以当年官方发布为准。</span></p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowRight,
  Calendar,
  CircleCheck,
  DataAnalysis,
  DocumentChecked,
  InfoFilled,
  Key,
  Lock,
  Message,
  TrendCharts,
  User
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { resetPassword, sendPasswordResetCode, sendRegistrationCode } from '../api'
import TurnstileWidget from '../components/TurnstileWidget.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const REMEMBERED_USERNAME_KEY = 'exam-study-hub:remembered-username'
const LEGACY_REMEMBERED_LOGIN_KEY = 'exam-study-hub:remembered-login'
const rememberedUsername = readRememberedUsername()

const mode = ref('login')
const loading = ref(false)
const sendingCode = ref(false)
const countdown = ref(0)
const turnstileToken = ref('')
const sentEmail = ref('')
const turnstileRef = ref()
const turnstileSiteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY || ''
const rememberUsername = ref(Boolean(rememberedUsername))
const formRef = ref()
const form = reactive({
  username: rememberedUsername,
  password: '',
  email: '',
  verificationCode: ''
})

const forgotOpen = ref(false)
const resetLoading = ref(false)
const sendingResetCode = ref(false)
const resetCountdown = ref(0)
const resetTurnstileToken = ref('')
const sentResetEmail = ref('')
const resetTurnstileRef = ref()
const resetFormRef = ref()
const resetForm = reactive({
  email: '',
  verificationCode: '',
  newPassword: '',
  confirmPassword: ''
})

let countdownTimer
let resetCountdownTimer

const normalizedEmail = computed(() => form.email.trim().toLowerCase())
const codeSentForCurrentEmail = computed(() => (
  Boolean(sentEmail.value) && sentEmail.value === normalizedEmail.value
))
const normalizedResetEmail = computed(() => resetForm.email.trim().toLowerCase())
const resetCodeSentForCurrentEmail = computed(() => (
  Boolean(sentResetEmail.value) && sentResetEmail.value === normalizedResetEmail.value
))

onMounted(() => {
  window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
})

const rules = {
  username: [{ required: true, min: 2, max: 64, message: '请输入 2-64 个字符的用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  verificationCode: [
    { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为 6 位数字', trigger: 'blur' }
  ]
}

const validateConfirmPassword = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入新密码'))
  } else if (value !== resetForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const resetRules = {
  email: [
    { required: true, message: '请输入注册邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  verificationCode: [
    { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为 6 位数字', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, min: 6, max: 128, message: '密码长度需为 6-128 位', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }]
}

// 切换登录/注册时清掉上一次的校验提示
watch(mode, () => {
  formRef.value?.clearValidate()
  turnstileToken.value = ''
})

watch(normalizedEmail, email => {
  if (sentEmail.value && sentEmail.value !== email) form.verificationCode = ''
})

watch(normalizedResetEmail, email => {
  if (sentResetEmail.value && sentResetEmail.value !== email) {
    resetForm.verificationCode = ''
    sentResetEmail.value = ''
    resetCountdown.value = 0
    window.clearInterval(resetCountdownTimer)
  }
})

watch(rememberUsername, remember => {
  if (!remember) clearRememberedUsername()
})

function readRememberedUsername() {
  try {
    // 旧版本曾把账号和密码一起保存在本地，升级后立即清除这份明文数据。
    localStorage.removeItem(LEGACY_REMEMBERED_LOGIN_KEY)
    return localStorage.getItem(REMEMBERED_USERNAME_KEY) || ''
  } catch {
    return ''
  }
}

function saveRememberedUsername() {
  localStorage.setItem(REMEMBERED_USERNAME_KEY, form.username)
}

function clearRememberedUsername() {
  localStorage.removeItem(REMEMBERED_USERNAME_KEY)
  localStorage.removeItem(LEGACY_REMEMBERED_LOGIN_KEY)
}

function syncRememberPreference() {
  if (rememberUsername.value) {
    saveRememberedUsername()
  } else {
    clearRememberedUsername()
  }
}

function handleTurnstileVerified(token) {
  turnstileToken.value = token
}

function handleTurnstileError() {
  turnstileToken.value = ''
  ElMessage.error('人机验证加载失败，请刷新后重试')
}

function startCountdown(seconds) {
  window.clearInterval(countdownTimer)
  countdown.value = seconds
  countdownTimer = window.setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) window.clearInterval(countdownTimer)
  }, 1000)
}

function startResetCountdown(seconds) {
  window.clearInterval(resetCountdownTimer)
  resetCountdown.value = seconds
  resetCountdownTimer = window.setInterval(() => {
    resetCountdown.value -= 1
    if (resetCountdown.value <= 0) window.clearInterval(resetCountdownTimer)
  }, 1000)
}

async function sendCode() {
  const emailValid = await formRef.value.validateField('email').then(() => true).catch(() => false)
  if (!emailValid) return
  if (!turnstileToken.value) {
    ElMessage.warning('请先完成人机验证')
    return
  }

  sendingCode.value = true
  try {
    const result = await sendRegistrationCode({
      email: normalizedEmail.value,
      turnstile_token: turnstileToken.value
    })
    sentEmail.value = normalizedEmail.value
    form.verificationCode = ''
    startCountdown(result.resend_after || 60)
    ElMessage.success('验证码已发送，请查收邮件')
  } catch (error) {
    ElMessage.error(error.message || '验证码发送失败，请稍后重试')
  } finally {
    sendingCode.value = false
    turnstileRef.value?.reset()
  }
}

async function openForgotPassword() {
  const loginEmail = normalizedEmail.value
  const currentResetEmail = normalizedResetEmail.value
  const keepCurrentFlow = Boolean(
    sentResetEmail.value
    && sentResetEmail.value === currentResetEmail
    && (!loginEmail || loginEmail === currentResetEmail)
  )

  resetForm.email = loginEmail || currentResetEmail
  if (!keepCurrentFlow) {
    resetForm.verificationCode = ''
    resetForm.newPassword = ''
    resetForm.confirmPassword = ''
    sentResetEmail.value = ''
    resetCountdown.value = 0
    window.clearInterval(resetCountdownTimer)
  }
  resetTurnstileToken.value = ''
  forgotOpen.value = true
  await nextTick()
  resetFormRef.value?.clearValidate()
}

function handleResetTurnstileVerified(token) {
  resetTurnstileToken.value = token
}

function handleResetTurnstileError() {
  resetTurnstileToken.value = ''
  ElMessage.error('人机验证加载失败，请刷新后重试')
}

async function sendResetCode() {
  const emailValid = await resetFormRef.value.validateField('email').then(() => true).catch(() => false)
  if (!emailValid) return
  if (!resetTurnstileToken.value) {
    ElMessage.warning('请先完成人机验证')
    return
  }

  sendingResetCode.value = true
  try {
    const result = await sendPasswordResetCode({
      email: normalizedResetEmail.value,
      turnstile_token: resetTurnstileToken.value
    })
    sentResetEmail.value = normalizedResetEmail.value
    resetForm.verificationCode = ''
    startResetCountdown(result.resend_after || 60)
    ElMessage.success('如果该邮箱已注册，验证码已发送，请查收邮件')
  } catch (error) {
    ElMessage.error(error.message || '验证码发送失败，请稍后重试')
  } finally {
    sendingResetCode.value = false
    resetTurnstileRef.value?.reset()
  }
}

async function submitPasswordReset() {
  const valid = await resetFormRef.value.validate().catch(() => false)
  if (!valid) return
  if (!resetCodeSentForCurrentEmail.value) {
    ElMessage.warning('请先获取当前邮箱的验证码')
    return
  }

  resetLoading.value = true
  try {
    await resetPassword({
      email: normalizedResetEmail.value,
      verification_code: resetForm.verificationCode,
      new_password: resetForm.newPassword
    })
    forgotOpen.value = false
    form.password = ''
    resetForm.email = ''
    resetForm.verificationCode = ''
    resetForm.newPassword = ''
    resetForm.confirmPassword = ''
    sentResetEmail.value = ''
    resetCountdown.value = 0
    window.clearInterval(resetCountdownTimer)
    ElMessage.success('密码已重置，请使用新密码登录')
  } catch (error) {
    ElMessage.error(error.message || '密码重置失败，请稍后重试')
  } finally {
    resetLoading.value = false
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
      if (!codeSentForCurrentEmail.value) {
        ElMessage.warning('请先获取当前邮箱的验证码')
        return
      }
      await auth.register({
        username: form.username,
        password: form.password,
        email: normalizedEmail.value,
        verification_code: form.verificationCode
      })
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

onBeforeUnmount(() => {
  window.clearInterval(countdownTimer)
  window.clearInterval(resetCountdownTimer)
})
</script>

<style scoped lang="less" src="../styles/views/Login.less"></style>
