<template>
  <div class="practice-page page-stack">
    <section class="page-intro">
      <div>
        <span class="section-kicker">任务练习</span>
        <h2>{{ subject }} · {{ activeGroup?.name || requestedTopic || '知识点练习' }}</h2>
        <p>完成这组题后，结果会进入学习进度，并据此调整复习队列。</p>
      </div>
      <el-button @click="router.push('/plan')">返回学习路线</el-button>
    </section>

    <el-alert v-if="store.targetDatePassed" type="warning" show-icon :closable="false"
      title="目标达标日已到期，请先调整报考年度，再继续按计划练习。" />
    <el-card v-else-if="loading" shadow="never">正在加载题目…</el-card>
    <el-alert v-else-if="error" type="error" show-icon :closable="false" :title="error">
      <template #default><el-button text type="primary" @click="loadGroups">重试</el-button></template>
    </el-alert>
    <el-empty v-else-if="!groups.length" description="当前科目暂无可用题目，请稍后再试" />

    <template v-else>
      <el-alert v-if="requestedTopic && !hasRequestedTopic" type="info" show-icon :closable="false"
        :title="`暂未找到“${requestedTopic}”的对应题组，已打开本科目可用知识点；本次练习不会自动完成原任务。`" />
      <el-card shadow="never" class="practice-card">
        <div class="practice-toolbar">
          <div><strong>选择知识点</strong><small>{{ activeGroup?.questions.length || 0 }} 道题 · 正确率达到 60% 后计为一次有效复习</small></div>
          <el-select v-model="activeGroupId" filterable aria-label="练习知识点" class="topic-select">
            <el-option v-for="group in groups" :key="group.id" :label="group.name" :value="group.id" />
          </el-select>
        </div>
        <div v-if="activeGroup" class="practice-questions">
          <article v-for="(question, index) in activeGroup.questions" :key="question.id" class="practice-question">
            <h3>{{ index + 1 }}. {{ question.stem }}</h3>
            <el-radio-group v-model="answers[question.id]" :disabled="Boolean(result)" class="practice-options">
              <el-radio v-for="(option, optionIndex) in question.options" :key="optionIndex" :value="letters[optionIndex]" border>
                {{ letters[optionIndex] }}. {{ option }}
              </el-radio>
            </el-radio-group>
            <p v-if="result" :class="answers[question.id] === question.answer ? 'correct' : 'wrong'">
              {{ answers[question.id] === question.answer ? '回答正确' : `你的答案：${answers[question.id]} · 正确答案：${question.answer}` }}
            </p>
          </article>
        </div>
        <div class="practice-actions">
          <span v-if="result">本次答对 {{ result.correctCount }}/{{ result.totalQuestions }} 题，正确率 {{ result.accuracy }}%。{{ result.accuracy < 60 ? '该知识点已加入后续复习。' : '本次结果已记录。' }}</span>
          <span v-else>已完成 {{ answeredCount }}/{{ activeGroup?.questions.length || 0 }} 题</span>
          <el-button v-if="result" type="primary" plain @click="resetAnswers">再练一次</el-button>
          <el-button v-else type="primary" :disabled="!activeGroup?.questions.length || answeredCount < activeGroup.questions.length" @click="submit">提交并记录结果</el-button>
        </div>
      </el-card>
      <el-button v-if="result" class="back-plan" @click="router.push('/plan')">返回今日任务</el-button>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchDiagnosticGroups } from '../data/diagnostic-questions'
import { useApplicationStore } from '../stores/application'

const route = useRoute()
const router = useRouter()
const store = useApplicationStore()
const letters = ['A', 'B', 'C', 'D']
const subject = computed(() => {
  const available = store.selectedMajor?.subjects || []
  const requested = String(route.query.subject || '')
  return available.includes(requested) ? requested : available[0] || ''
})
const requestedTopic = computed(() => String(route.query.topic || ''))
const groups = ref([])
const activeGroupId = ref('')
const loading = ref(true)
const error = ref('')
const answers = reactive({})
const result = ref(null)
const activeGroup = computed(() => groups.value.find(group => group.id === activeGroupId.value))
const hasRequestedTopic = computed(() => groups.value.some(group => group.name === requestedTopic.value))
const answeredCount = computed(() => activeGroup.value?.questions.filter(question => answers[question.id] != null).length || 0)

async function loadGroups() {
  loading.value = true
  error.value = ''
  try {
    groups.value = (await fetchDiagnosticGroups([subject.value])).filter(group => group.questions?.length)
    activeGroupId.value = (groups.value.find(group => group.name === requestedTopic.value) || groups.value[0])?.id || ''
  } catch {
    error.value = '题目加载失败，请检查网络后重试。'
  } finally {
    loading.value = false
  }
}

watch(activeGroupId, () => resetAnswers())
function resetAnswers() {
  Object.keys(answers).forEach(key => delete answers[key])
  result.value = null
}

function submit() {
  if (!activeGroup.value?.questions.length || answeredCount.value !== activeGroup.value.questions.length) return
  const correctCount = activeGroup.value.questions.filter(question => answers[question.id] === question.answer).length
  result.value = store.recordPracticeResult({
    subject: subject.value,
    knowledgeName: activeGroup.value.name,
    correctCount,
    totalQuestions: activeGroup.value.questions.length,
    taskId: route.query.taskId,
    taskDate: route.query.taskDate,
  })
}

onMounted(loadGroups)
</script>

<style scoped>
.practice-page { display: flex; flex-direction: column; gap: 18px; max-width: 900px; margin: 0 auto; width: 100%; }
.page-intro { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.page-intro h2 { color: var(--ink); font-size: 1.55rem; }
.page-intro p { margin-top: 5px; color: var(--text-secondary); }
.section-kicker { display: block; margin-bottom: 5px; color: var(--primary); font-size: .72rem; font-weight: 800; letter-spacing: .08em; }
.practice-card { border-radius: 18px; }
.practice-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.practice-toolbar strong, .practice-toolbar small { display: block; }
.practice-toolbar small { margin-top: 5px; color: var(--text-muted); font-size: .75rem; }
.topic-select { width: min(320px, 100%); }
.practice-question { padding: 20px 0; border-top: 1px solid var(--line); }
.practice-question h3 { margin-bottom: 14px; color: var(--ink); font-size: .95rem; line-height: 1.55; }
.practice-options { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; width: 100%; }
.practice-options :deep(.el-radio) { width: 100%; height: auto; min-height: 44px; margin: 0; padding: 9px 12px; white-space: normal; }
.practice-question p { margin-top: 10px; font-size: .8rem; font-weight: 700; }
.practice-question p.correct { color: #15815f; }
.practice-question p.wrong { color: #be5b3c; }
.practice-actions { display: flex; align-items: center; justify-content: space-between; gap: 14px; border-top: 1px solid var(--line); padding-top: 20px; }
.practice-actions span { color: var(--text-secondary); font-size: .82rem; }
.back-plan { align-self: flex-end; }
@media (max-width: 650px) {
  .page-intro { flex-direction: column; }
  .practice-toolbar, .practice-actions { flex-direction: column; align-items: stretch; }
  .practice-options { grid-template-columns: 1fr; }
  .topic-select { width: 100%; }
}
</style>
