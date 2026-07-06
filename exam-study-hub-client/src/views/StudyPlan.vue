<template>
  <div class="plan-page page-stack">
    <section class="page-intro"><div><span class="section-kicker">STEP 05</span><h2>{{ store.profile.mode==='plan'?'我的最短达标计划':'我的自主学习路线' }}</h2><p>距考试 {{ store.daysUntilExam }} 天（{{ store.examDate }}） · 每周 {{ store.weeklyHours }} 小时 · 目标 {{ store.targetScore }} 分</p></div><el-tag size="large">{{ store.profile.mode==='plan'?'计划模式':'自主模式' }}</el-tag></section>

    <section class="stage-overview"><div v-for="stage in store.planMilestones" :key="stage.id" class="stage-node" :class="stage.status"><span><el-icon v-if="stage.status==='completed'"><Check /></el-icon><template v-else>{{ stage.id }}</template></span><div><small>阶段 {{ stage.id }}</small><strong>{{ stage.name }}</strong><p>{{ stage.startDate.slice(5) }} ~ {{ stage.endDate.slice(5) }}</p></div></div></section>

    <section v-if="topWeaknesses.length" class="route-evidence">
      <div>
        <span class="section-kicker">路线依据</span>
        <h3>优先处理 {{ topWeaknesses[0].subject }} · {{ topWeaknesses[0].name }}</h3>
        <p>{{ topWeaknesses[0].reason }}，当前路线会先补短板，再进入专项和真题迁移。</p>
      </div>
      <div class="weakness-list">
        <span v-for="point in topWeaknesses" :key="`${point.subject}-${point.id}`" :class="point.severity">
          <b>{{ point.subject }}</b>{{ point.name }}<em>{{ point.mastery }}%</em>
        </span>
      </div>
    </section>

    <section class="route-loop">
      <article>
        <small>当前策略</small>
        <strong>{{ store.planMode.label }}</strong>
        <p>{{ store.planMode.description }}</p>
      </article>
      <article>
        <small>今日复习</small>
        <strong>{{ store.reviewStats.due }}</strong>
        <p>{{ store.reviewStats.scheduled }} 个错题知识点已排入后续复习。</p>
      </article>
      <article>
        <small>闭环规则</small>
        <strong>3 轮</strong>
        <p>错题复习连续掌握后自动降权，并从复习队列移出。</p>
      </article>
    </section>

    <section class="plan-layout">
      <div class="stage-detail">
        <el-card v-for="stage in store.planMilestones" :key="stage.id" shadow="never" class="stage-card" :class="stage.status">
          <div class="stage-card-head"><span class="stage-badge">0{{ stage.id }}</span><div><h3>{{ stage.name }}</h3><p>{{ stage.description }}</p></div><el-tag :type="statusType(stage.status)" effect="plain">{{ statusLabel(stage.status) }}</el-tag></div>
          <div class="stage-goal"><el-icon><Flag /></el-icon><span><small>阶段完成标准</small><strong>{{ stage.target }}</strong></span></div>
          <div v-if="stage.focusPoints?.length" class="stage-focus">
            <div class="stage-focus-head"><strong>{{ stage.focusTitle }}</strong><span>{{ stage.focusSummary }}</span></div>
            <div class="focus-points">
              <span v-for="point in stage.focusPoints" :key="`${stage.id}-${point.subject}-${point.id}`"><b>{{ point.subject }}</b>{{ point.name }}<em>{{ point.mastery }}%</em></span>
            </div>
          </div>
          <div class="stage-window"><el-icon><Calendar /></el-icon><span>{{ stage.startDate }} ~ {{ stage.endDate }}</span></div>
          <div v-if="stage.status==='active'" class="active-actions"><el-button type="primary" plain @click="openStageTest">进行阶段测试</el-button><span>优先抽取本阶段重点；偏低时自动把薄弱知识点加入复习队列。</span></div>
        </el-card>
      </div>

      <aside class="daily-panel">
        <div class="daily-head"><div><span class="section-kicker">{{ store.profile.mode==='plan'?'今天':'当前建议' }}</span><h3>{{ store.profile.mode==='plan'?`完成 ${store.tasks.length} 项任务`:'基础建立阶段' }}</h3></div><el-progress type="circle" :percentage="store.overallProgress" :width="64" :stroke-width="7" /></div>
        <p v-if="store.profile.mode==='plan' && store.reviewStats.due" class="review-note"><el-icon><Warning /></el-icon> 有 {{ store.reviewStats.due }} 个错题知识点今日到期，已排入任务。</p>
        <p v-else-if="store.profile.mode==='plan' && store.reviewStats.scheduled" class="review-note scheduled"><el-icon><Calendar /></el-icon> {{ store.reviewStats.scheduled }} 个错题知识点已排到后续复习日。</p>
        <template v-if="store.profile.mode==='plan'">
          <div v-for="group in tasksBySubject" :key="group.subject" class="task-group">
            <div class="task-group-head"><span class="task-subject">{{ group.subject }}</span><small>{{ group.doneCount }}/{{ group.tasks.length }} 项 · {{ group.minutes }} 分钟</small></div>
            <div v-for="task in group.tasks" :key="task.id" class="task-row" :class="{done:task.done, review: task.reviewKey, focus: task.focus, sprint: task.sprint}">
              <el-checkbox :model-value="task.done" @change="store.toggleTask(task.id)"/>
              <span>
                <strong>{{ task.title }}</strong>
                <small>
                  {{ task.type }} · {{ task.duration }} 分钟
                  <span v-if="task.mastery != null"> · 掌握度 {{ task.mastery }}%</span>
                  <span v-if="task.reviewKey"> · 连续掌握 {{ task.masteryHits || 0 }}/3</span>
                  <span v-if="task.sprint"> · {{ task.modeLabel }}</span>
                </small>
              </span>
            </div>
          </div>
        </template>
        <div v-else class="self-panel">
          <p class="self-intro">自主模式不生成每日排期。左侧四个阶段会按诊断薄弱项给出重点，下面按优先级列出当前最该推进的知识点。</p>
          <ol v-if="selfOrder.length" class="self-order">
            <li v-for="point in selfOrder" :key="point.id">
              <div class="self-order-top"><strong>{{ point.name }}</strong><b :class="point.mastery < 60 ? 'weak' : ''">{{ point.mastery }}%</b></div>
              <small>{{ point.subject }} · 答对 {{ point.correct }}/{{ point.total }}</small>
            </li>
          </ol>
          <el-empty v-else description="完成入学诊断后，这里会按薄弱知识点给出建议学习顺序" :image-size="60" />
        </div>
      </aside>
    </section>

    <el-dialog v-model="testDialog" :title="`阶段 ${testingStage} · ${currentStageName}测试`" width="min(760px, 94vw)" top="4vh" class="stage-test-dialog" destroy-on-close>
      <template v-if="!testResult">
        <div class="test-intro">
          <div><strong>{{ answeredTestCount }}/{{ stageQuestions.length }}</strong><span>已完成</span></div>
          <el-progress :percentage="testProgress" :stroke-width="9" :show-text="false" />
          <p>题目来自本阶段相关知识点，系统将按正确率自动判分。</p>
        </div>

        <el-empty v-if="!hasStageQuestions" description="当前科目题库暂不可用，请稍后再试或先继续复习" :image-size="72" />
        <div v-else class="stage-question-list">
          <article v-for="(question, index) in stageQuestions" :key="question.id" class="stage-question">
            <div class="stage-question-meta"><span class="question-order">{{ String(index + 1).padStart(2, '0') }}</span><el-tag size="small" effect="plain">{{ question.subject }} · {{ question.knowledgeName }}</el-tag></div>
            <h4>{{ question.stem }}</h4>
            <el-radio-group v-model="testAnswers[question.id]" class="stage-options">
              <el-radio v-for="(option, optionIndex) in question.options" :key="option" :value="optionLetters[optionIndex]" border><b>{{ optionLetters[optionIndex] }}</b>{{ option }}</el-radio>
            </el-radio-group>
          </article>
        </div>
      </template>

      <div v-else class="test-result-panel">
        <span class="result-mark" :class="testResult.passed ? 'passed' : 'review'"><el-icon><component :is="testResult.passed ? 'CircleCheck' : 'Warning'" /></el-icon></span>
        <h3>{{ testResult.passed ? '本阶段已达标' : '建议先补一次薄弱知识点' }}</h3>
        <p>答对 {{ testResult.correctCount }}/{{ testResult.totalQuestions }} 题，正确率 {{ testResult.accuracy }}%，本阶段标准为 {{ testResult.threshold }}%。</p>
        <div class="auto-score"><span><small>系统折算分</small><strong>{{ testResult.score }}</strong></span><span><small>薄弱知识点</small><strong>{{ testResult.weakKnowledge || '暂无明显薄弱项' }}</strong></span></div>
        <el-alert v-if="testResult.queuedReviewCount" :title="`${testResult.queuedReviewCount} 个错题知识点已进入 ${testResult.nextReviewDate} 复习；连续掌握 3 轮后会自动降权移出。`" type="info" show-icon :closable="false" />
        <el-alert v-if="testResult.stabilizedReviewCount" :title="`${testResult.stabilizedReviewCount} 个旧错题已连续掌握，已从复习队列移出。`" type="success" show-icon :closable="false" />
        <el-alert v-if="!testResult.passed" title="你可以关闭测试继续复习，也可以忽略建议进入下一阶段。" type="warning" show-icon :closable="false" />
      </div>

      <template #footer>
        <template v-if="!testResult"><el-button @click="testDialog=false">稍后再测</el-button><el-button type="primary" :disabled="!hasStageQuestions || answeredTestCount < stageQuestions.length" @click="submitTest">提交并自动判分</el-button></template>
        <template v-else-if="testResult.passed"><el-button type="primary" @click="testDialog=false">完成，进入下一阶段</el-button></template>
        <template v-else><el-button @click="testDialog=false">留在本阶段复习</el-button><el-button type="primary" plain @click="continueAnyway">仍进入下一阶段</el-button></template>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { fetchDiagnosticGroups } from '../data/diagnostic-questions'
import { useApplicationStore } from '../stores/application'

const store = useApplicationStore()
const testDialog = ref(false)
const testResult = ref(null)
const testingStage = ref(store.currentStage)
const testAnswers = reactive({})
const optionLetters = ['A', 'B', 'C', 'D']
const allGroups = ref([])

onMounted(async () => {
  store.ensureTodayTasks()
  allGroups.value = await fetchDiagnosticGroups(store.selectedMajor?.subjects || [])
})

const statusLabel = status => ({ completed: '已完成', active: '进行中', pending: '未开始' })[status]
const statusType = status => ({ completed: 'success', active: 'primary', pending: 'info' })[status]
const currentStageName = computed(() => store.stages.find(stage => stage.id === testingStage.value)?.name || '')
const topWeaknesses = computed(() => store.weaknessBacklog.slice(0, 5))
const testingStageFocus = computed(() => store.stageFocusPlan.find(stage => stage.id === testingStage.value))

// 自主模式的建议学习顺序：各科知识点按掌握度从低到高排序，取最弱的若干个。
const selfOrder = computed(() => {
  return store.weaknessBacklog.slice(0, 8)
})

// 计划模式：把当日任务按科目分组，并按专业的科目顺序排列。
const tasksBySubject = computed(() => {
  const order = store.selectedMajor?.subjects || []
  const map = new Map()
  store.tasks.forEach(task => {
    if (!map.has(task.subject)) map.set(task.subject, [])
    map.get(task.subject).push(task)
  })
  const subjects = [...new Set([...order, ...map.keys()])].filter(subject => map.has(subject))
  return subjects.map(subject => {
    const tasks = map.get(subject)
    return {
      subject,
      tasks,
      doneCount: tasks.filter(task => task.done).length,
      minutes: tasks.reduce((sum, task) => sum + (task.duration || 0), 0)
    }
  })
})

const focusedQuestionGroups = computed(() => {
  const points = testingStageFocus.value?.focusPoints || []
  return points.map(point => allGroups.value.find(group =>
    group.subject === point.subject &&
    (String(group.id) === String(point.id) || group.name === point.name)
  )).filter(Boolean)
})

const stageQuestions = computed(() => {
  const focusGroups = focusedQuestionGroups.value.filter(group => group.questions?.length)
  if (focusGroups.length) {
    return focusGroups
      .flatMap(group => group.questions.slice(0, 2).map(question => ({ ...question, subject: group.subject, knowledgeName: group.name })))
      .slice(0, 8)
  }
  const subjects = store.selectedMajor?.subjects || []
  const groups = allGroups.value
  return subjects.flatMap(subject => {
    const subjectGroups = groups.filter(group => group.subject === subject)
    if (!subjectGroups.length) return []
    const selectedGroup = testingStage.value === 1
      ? subjectGroups[0]
      : testingStage.value === 2
        ? subjectGroups[1] || subjectGroups[0]
        : null
    const questions = selectedGroup
      ? selectedGroup.questions.slice(0, 2).map(question => ({ ...question, subject, knowledgeName: selectedGroup.name }))
      : subjectGroups.flatMap(group => group.questions.slice(0, 1).map(question => ({ ...question, subject, knowledgeName: group.name }))).slice(0, 2)
    return questions
  })
})

const answeredTestCount = computed(() => stageQuestions.value.filter(question => testAnswers[question.id] !== undefined).length)
const hasStageQuestions = computed(() => stageQuestions.value.length > 0)
const testProgress = computed(() => Math.round(answeredTestCount.value / Math.max(stageQuestions.value.length, 1) * 100))

function openStageTest() {
  testingStage.value = store.currentStage
  testResult.value = null
  Object.keys(testAnswers).forEach(key => delete testAnswers[key])
  testDialog.value = true
}

function submitTest() {
  if (!hasStageQuestions.value || answeredTestCount.value < stageQuestions.value.length) return
  const correctQuestions = stageQuestions.value.filter(question => testAnswers[question.id] === question.answer)
  const correctCount = correctQuestions.length
  const totalQuestions = stageQuestions.value.length
  const accuracy = Math.round(correctCount / totalQuestions * 100)
  const wrongQuestions = stageQuestions.value.filter(question => testAnswers[question.id] !== question.answer)
  const wrongKnowledge = wrongQuestions
    .reduce((counts, question) => ({ ...counts, [question.knowledgeName]: (counts[question.knowledgeName] || 0) + 1 }), {})
  const weakKnowledge = Object.entries(wrongKnowledge).sort((a, b) => b[1] - a[1])[0]?.[0] || ''
  // 答错知识点去重后作为复习项传给 store（动态纠偏）
  const seen = new Set()
  const weakPoints = []
  const testedSeen = new Set()
  const testedPoints = []
  stageQuestions.value.forEach(question => {
    const key = `${question.subject}:${question.knowledgeName}`
    if (!testedSeen.has(key)) {
      testedSeen.add(key)
      testedPoints.push({ subject: question.subject, knowledgeName: question.knowledgeName })
    }
  })
  wrongQuestions.forEach(question => {
    const key = `${question.subject}:${question.knowledgeName}`
    if (!seen.has(key)) {
      seen.add(key)
      weakPoints.push({ subject: question.subject, knowledgeName: question.knowledgeName })
    }
  })
  const score = Math.round(accuracy / 100 * 450)
  const result = store.submitStageTest({ score, accuracy, correctCount, totalQuestions, weakKnowledge, weakPoints, testedPoints })
  testResult.value = { ...result, score, accuracy, correctCount, totalQuestions, weakKnowledge }
}

function continueAnyway() {
  store.advanceStage()
  testDialog.value = false
}
</script>

<style scoped lang="less" src="../styles/views/StudyPlan.less"></style>
