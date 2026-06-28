<template>
  <div class="plan-page page-stack">
    <section class="page-intro"><div><span class="section-kicker">STEP 05</span><h2>{{ store.profile.mode==='plan'?'我的最短达标计划':'我的自主学习路线' }}</h2><p>距考试 {{ store.daysUntilExam }} 天（{{ store.examDate }}） · 每周 {{ store.weeklyHours }} 小时 · 目标 {{ store.targetScore }} 分</p></div><el-tag size="large">{{ store.profile.mode==='plan'?'计划模式':'自主模式' }}</el-tag></section>

    <section class="stage-overview"><div v-for="stage in store.planMilestones" :key="stage.id" class="stage-node" :class="stage.status"><span><el-icon v-if="stage.status==='completed'"><Check /></el-icon><template v-else>{{ stage.id }}</template></span><div><small>阶段 {{ stage.id }}</small><strong>{{ stage.name }}</strong><p>{{ stage.startDate.slice(5) }} ~ {{ stage.endDate.slice(5) }}</p></div></div></section>

    <section class="plan-layout">
      <div class="stage-detail">
        <el-card v-for="stage in store.planMilestones" :key="stage.id" shadow="never" class="stage-card" :class="stage.status">
          <div class="stage-card-head"><span class="stage-badge">0{{ stage.id }}</span><div><h3>{{ stage.name }}</h3><p>{{ stage.description }}</p></div><el-tag :type="statusType(stage.status)" effect="plain">{{ statusLabel(stage.status) }}</el-tag></div>
          <div class="stage-goal"><el-icon><Flag /></el-icon><span><small>阶段完成标准</small><strong>{{ stage.target }}</strong></span></div>
          <div class="stage-window"><el-icon><Calendar /></el-icon><span>{{ stage.startDate }} ~ {{ stage.endDate }}</span></div>
          <div v-if="stage.status==='active'" class="active-actions"><el-button type="primary" plain @click="openStageTest">进行阶段测试</el-button><span>系统出题并自动判分；偏低时自动把薄弱知识点加入明日复习，不强制退回。</span></div>
        </el-card>
      </div>

      <aside class="daily-panel">
        <div class="daily-head"><div><span class="section-kicker">{{ store.profile.mode==='plan'?'今天':'当前建议' }}</span><h3>{{ store.profile.mode==='plan'?`完成 ${store.tasks.length} 项任务`:'基础建立阶段' }}</h3></div><el-progress type="circle" :percentage="store.overallProgress" :width="64" :stroke-width="7" /></div>
        <p v-if="store.profile.mode==='plan' && store.reviewQueue.length" class="review-note"><el-icon><Warning /></el-icon> 有 {{ store.reviewQueue.length }} 个薄弱知识点待复习，已排入今日任务。</p>
        <template v-if="store.profile.mode==='plan'">
          <div v-for="group in tasksBySubject" :key="group.subject" class="task-group">
            <div class="task-group-head"><span class="task-subject">{{ group.subject }}</span><small>{{ group.doneCount }}/{{ group.tasks.length }} 项 · {{ group.minutes }} 分钟</small></div>
            <div v-for="task in group.tasks" :key="task.id" class="task-row" :class="{done:task.done, review: task.reviewKey}"><el-checkbox :model-value="task.done" @change="store.toggleTask(task.id)"/><span><strong>{{ task.title }}</strong><small>{{ task.type }} · {{ task.duration }} 分钟</small></span></div>
          </div>
        </template>
        <div v-else class="self-panel">
          <p class="self-intro">自主模式不生成每日排期。左侧四个阶段为统一路线，按下面「掌握度从低到高」的顺序优先推进，达到各阶段完成标准后再做阶段测试。</p>
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

        <div class="stage-question-list">
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
        <el-alert v-if="!testResult.passed" title="你可以关闭测试继续复习，也可以忽略建议进入下一阶段。" type="warning" show-icon :closable="false" />
      </div>

      <template #footer>
        <template v-if="!testResult"><el-button @click="testDialog=false">稍后再测</el-button><el-button type="primary" :disabled="answeredTestCount < stageQuestions.length" @click="submitTest">提交并自动判分</el-button></template>
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

// 自主模式的建议学习顺序：各科知识点按掌握度从低到高排序，取最弱的若干个。
const selfOrder = computed(() => {
  const points = store.subjectTargets.flatMap(st => (st.knowledgePoints || []).map(p => ({ ...p, subject: st.name })))
  return points.sort((a, b) => a.mastery - b.mastery).slice(0, 8)
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

const stageQuestions = computed(() => {
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
const testProgress = computed(() => Math.round(answeredTestCount.value / Math.max(stageQuestions.value.length, 1) * 100))

function openStageTest() {
  testingStage.value = store.currentStage
  testResult.value = null
  Object.keys(testAnswers).forEach(key => delete testAnswers[key])
  testDialog.value = true
}

function submitTest() {
  if (answeredTestCount.value < stageQuestions.value.length) return
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
  wrongQuestions.forEach(question => {
    if (!seen.has(question.knowledgeName)) {
      seen.add(question.knowledgeName)
      weakPoints.push({ subject: question.subject, knowledgeName: question.knowledgeName })
    }
  })
  const score = Math.round(accuracy / 100 * 450)
  const result = store.submitStageTest({ score, accuracy, correctCount, totalQuestions, weakKnowledge, weakPoints })
  testResult.value = { ...result, score, accuracy, correctCount, totalQuestions, weakKnowledge }
}

function continueAnyway() {
  store.advanceStage()
  testDialog.value = false
}
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}.page-intro{display:flex;align-items:flex-start;justify-content:space-between}.page-intro h2{color:var(--ink);font-size:1.7rem}.page-intro p{margin-top:5px;color:var(--text-secondary)}.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}.stage-overview{display:grid;grid-template-columns:repeat(4,1fr);gap:0;padding:20px;border:1px solid var(--line);border-radius:18px;background:#fff}.stage-node{display:flex;align-items:center;gap:10px;position:relative}.stage-node:not(:last-child):after{content:'';position:absolute;right:10px;width:34%;height:2px;background:var(--line)}.stage-node>span{width:36px;height:36px;display:grid;place-items:center;border-radius:50%;color:var(--text-muted);font-weight:800;background:#edf1f6}.stage-node.active>span{color:#fff;background:var(--primary);box-shadow:0 0 0 6px var(--primary-soft)}.stage-node.completed>span{color:#fff;background:var(--mint)}.stage-node small,.stage-node strong,.stage-node p{display:block}.stage-node small{color:var(--text-muted);font-size:.64rem}.stage-node strong{color:var(--ink);font-size:.8rem}.stage-node p{color:var(--text-muted);font-size:.66rem}.plan-layout{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:18px;align-items:start}.stage-detail{display:flex;flex-direction:column;gap:12px}.stage-card{border-radius:18px;border-color:var(--line)}.stage-card.active{border-color:#8bb1f7;box-shadow:0 0 0 3px rgba(37,99,235,.07)}.stage-card-head{display:flex;align-items:center;gap:13px}.stage-badge{width:38px;height:38px;display:grid;place-items:center;border-radius:12px;color:var(--primary);font-weight:900;background:var(--primary-soft)}.stage-card-head>div{flex:1}.stage-card-head h3{color:var(--ink);font-size:.95rem}.stage-card-head p{color:var(--text-secondary);font-size:.74rem}.stage-goal{display:flex;align-items:center;gap:9px;margin-top:14px;padding:12px;border-radius:12px;background:#f6f8fc}.stage-goal>span small,.stage-goal>span strong{display:block}.stage-goal small{color:var(--text-muted);font-size:.66rem}.stage-goal strong{color:var(--ink);font-size:.76rem}.stage-window{display:flex;align-items:center;gap:7px;margin-top:9px;color:var(--text-secondary);font-size:.74rem}.stage-window .el-icon{color:var(--primary)}.review-note{display:flex;align-items:center;gap:6px;margin-top:14px;padding:9px 11px;border-radius:10px;color:#b77400;font-size:.74rem;background:var(--accent-soft)}.active-actions{display:flex;align-items:center;gap:12px;margin-top:13px}.active-actions span{color:var(--text-muted);font-size:.7rem}.daily-panel{position:sticky;top:98px;padding:22px;border:1px solid var(--line);border-radius:20px;background:#fff}.daily-head{display:flex;align-items:center;justify-content:space-between}.daily-head h3{color:var(--ink);font-size:1rem}.task-row{display:flex;align-items:flex-start;gap:9px;padding:14px 0;border-bottom:1px solid var(--line)}.task-row>span{flex:1}.task-row b{display:inline-block;padding:2px 6px;margin-bottom:5px;border-radius:5px;color:var(--primary);font-size:.65rem;background:var(--primary-soft)}.task-row strong,.task-row small{display:block}.task-row strong{color:var(--ink);font-size:.78rem}.task-row small{color:var(--text-muted);font-size:.68rem}.task-row.done{opacity:.55}.task-row.done strong{text-decoration:line-through}.task-group{margin-bottom:4px}.task-group-head{display:flex;align-items:baseline;justify-content:space-between;margin:14px 0 2px;padding-bottom:6px;border-bottom:2px solid var(--primary-soft)}.task-subject{color:var(--primary-deep);font-size:.82rem;font-weight:800}.task-group-head small{color:var(--text-muted);font-size:.68rem}.task-row.review{border-left:3px solid var(--accent);padding-left:8px;margin-left:-11px}.task-row.review strong{color:#b77400}.self-intro{margin-top:6px;padding:14px;border-radius:13px;color:var(--text-secondary);font-size:.76rem;line-height:1.6;background:#f6f8fc}.self-order{margin-top:14px;padding-left:0;list-style:none;counter-reset:self}.self-order li{counter-increment:self;position:relative;padding:11px 0 11px 30px;border-bottom:1px solid var(--line)}.self-order li:before{content:counter(self);position:absolute;left:0;top:11px;width:21px;height:21px;display:grid;place-items:center;border-radius:6px;color:var(--primary);font-size:.66rem;font-weight:800;background:var(--primary-soft)}.self-order-top{display:flex;align-items:baseline;justify-content:space-between}.self-order strong{color:var(--ink);font-size:.8rem}.self-order b{color:var(--mint);font-size:.8rem}.self-order b.weak{color:#e6a23c}.self-order small{display:block;margin-top:2px;color:var(--text-muted);font-size:.68rem}.test-intro{display:grid;grid-template-columns:100px 1fr;align-items:center;gap:14px;padding:16px 18px;border-radius:14px;background:#f5f8fc}.test-intro>div{display:flex;align-items:baseline;gap:5px}.test-intro strong{color:var(--ink);font-size:1.2rem}.test-intro span,.test-intro p{color:var(--text-muted);font-size:.7rem}.test-intro p{grid-column:1/-1;margin-top:-7px}.stage-question-list{display:flex;flex-direction:column;gap:14px;max-height:55vh;margin-top:16px;padding:0 10px 6px 0;overflow:auto;scrollbar-gutter:stable}.stage-question{padding:18px;border:1px solid var(--line);border-radius:14px;background:#fff}.stage-question-meta{display:flex;align-items:center;gap:9px;min-width:0}.stage-question-meta>.question-order{width:30px;height:30px;display:grid;place-items:center;flex:0 0 30px;border-radius:9px;color:var(--primary);font-size:.68rem;font-weight:900;background:var(--primary-soft)}.stage-question-meta :deep(.el-tag){max-width:calc(100% - 40px);height:26px;padding:0 9px;border-radius:7px;overflow:hidden;text-overflow:ellipsis}.stage-question h4{margin:14px 0;color:var(--ink);font-size:.9rem;line-height:1.55}.stage-options{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;width:100%}:deep(.stage-options .el-radio){width:100%;height:auto;min-height:44px;margin:0;padding:10px 12px;border-radius:10px}:deep(.stage-options .el-radio__label){display:flex;align-items:center;min-width:0;white-space:normal;line-height:1.4}.stage-options b{display:inline-grid;place-items:center;width:21px;height:21px;margin-right:7px;flex:0 0 21px;border-radius:5px;color:var(--text-secondary);font-size:.65rem;background:#eef2f7}.test-result-panel{text-align:center;padding:12px}.result-mark{width:58px;height:58px;display:grid;place-items:center;margin:0 auto 12px;border-radius:18px;font-size:28px}.result-mark.passed{color:var(--mint);background:var(--mint-soft)}.result-mark.review{color:#b77400;background:var(--accent-soft)}.test-result-panel h3{color:var(--ink);font-size:1.25rem}.test-result-panel>p{margin:6px 0 18px;color:var(--text-secondary);font-size:.8rem}.auto-score{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}.auto-score>span{padding:14px;border-radius:12px;text-align:left;background:#f5f8fc}.auto-score small,.auto-score strong{display:block}.auto-score small{color:var(--text-muted);font-size:.68rem}.auto-score strong{margin-top:3px;color:var(--ink);font-size:1rem}:deep(.stage-test-dialog .el-dialog__header){margin:0;padding:20px 22px 12px;border-bottom:1px solid var(--line)}:deep(.stage-test-dialog .el-dialog__body){padding:16px 22px}:deep(.stage-test-dialog .el-dialog__footer){padding:14px 22px;border-top:1px solid var(--line)}
@media(max-width:1050px){.stage-overview{grid-template-columns:repeat(2,1fr);gap:18px}.stage-node:after{display:none}.plan-layout{grid-template-columns:1fr}.daily-panel{position:static}}@media(max-width:600px){.stage-overview{grid-template-columns:1fr}.active-actions{align-items:flex-start;flex-direction:column}.stage-options,.auto-score{grid-template-columns:1fr}.test-intro{grid-template-columns:1fr}.test-intro p{grid-column:auto;margin:0}}
</style>
