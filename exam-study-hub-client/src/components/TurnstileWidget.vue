<template>
  <div class="turnstile-widget" role="group" aria-label="Cloudflare 人机验证">
    <div v-if="siteKey" ref="containerRef" class="turnstile-container"></div>
    <p v-else class="turnstile-config-error" role="alert">
      人机验证尚未配置，请联系管理员。
    </p>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  siteKey: { type: String, required: true }
})
const emit = defineEmits(['verified', 'expired', 'error'])

const containerRef = ref()
let widgetId

function loadTurnstileScript() {
  if (window.turnstile) return Promise.resolve(window.turnstile)
  if (window.__examStudyTurnstilePromise) return window.__examStudyTurnstilePromise

  window.__examStudyTurnstilePromise = new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-exam-study-turnstile]')
    if (existing) {
      existing.addEventListener('load', () => resolve(window.turnstile), { once: true })
      existing.addEventListener('error', reject, { once: true })
      return
    }

    const script = document.createElement('script')
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
    script.async = true
    script.defer = true
    script.dataset.examStudyTurnstile = 'true'
    script.onload = () => resolve(window.turnstile)
    script.onerror = reject
    document.head.appendChild(script)
  })
  return window.__examStudyTurnstilePromise
}

async function renderWidget() {
  if (!props.siteKey || !containerRef.value) return
  try {
    const turnstile = await loadTurnstileScript()
    await nextTick()
    if (!containerRef.value || widgetId !== undefined) return
    widgetId = turnstile.render(containerRef.value, {
      sitekey: props.siteKey,
      action: 'register',
      size: 'flexible',
      theme: 'light',
      callback: token => emit('verified', token),
      'expired-callback': () => emit('expired'),
      'error-callback': error => emit('error', error)
    })
  } catch {
    emit('error', '人机验证加载失败')
  }
}

function reset() {
  if (window.turnstile && widgetId !== undefined) window.turnstile.reset(widgetId)
  emit('expired')
}

onMounted(renderWidget)
onBeforeUnmount(() => {
  if (window.turnstile && widgetId !== undefined) window.turnstile.remove(widgetId)
})

defineExpose({ reset })
</script>

<style scoped>
.turnstile-widget,
.turnstile-container {
  width: 100%;
  min-height: 65px;
}

.turnstile-config-error {
  min-height: 48px;
  display: flex;
  align-items: center;
  margin: 0;
  padding: 10px 12px;
  border: 1px solid #f1c8c5;
  border-radius: 10px;
  color: #9f2d28;
  background: #fff7f6;
  font-size: 0.78rem;
  line-height: 1.5;
}
</style>
