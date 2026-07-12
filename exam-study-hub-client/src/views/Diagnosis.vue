<template>
  <div class="diagnosis-page page-stack">
    <section class="page-intro">
      <div>
        <span class="section-kicker">STEP 03</span>
        <h2>{{ store.diagnosisComplete ? '基础诊断报告' : '知识点基础诊断' }}</h2>
        <p>{{ store.diagnosisComplete ? '分数完全由答题结果生成，可随时重新测试。' : `共 ${groups.length} 个知识点、${totalQuestions} 道单选题，每个知识点 3~5 道。` }}</p>
      </div>
      <div class="intro-actions">
        <el-button v-if="auth.isAdmin && !store.diagnosisComplete" type="warning" plain size="small" @click="adminAutofill">
          <el-icon><MagicStick /></el-icon>随机填充并提交（测试）
        </el-button>
        <el-tag :type="store.diagnosisComplete ? 'success' : 'primary'" effect="light">
          {{ store.diagnosisComplete ? '诊断完成' : formatTime(elapsedSeconds) }}
        </el-tag>
      </div>
    </section>

    <template v-if="!store.diagnosisComplete">
      <section class="diagnosis-shell">
        <div class="diagnosis-summary">
          <div>
            <span>答题进度</span>
            <strong>{{ answeredCount }} / {{ totalQuestions }}</strong>
          </div>
          <el-progress :percentage="progressPercent" :stroke-width="10" :show-text="false" />
          <small>答错不会影响操作，请按真实基础作答；提交后系统会自动校对答案并生成薄弱项。</small>
        </div>

        <el-tabs v-model="activeSubject" class="subject-tabs" @tab-change="handleSubjectChange">
          <el-tab-pane v-for="subject in subjects" :key="subject" :name="subject">
            <template #label>
              <span class="subject-tab-label">
                <b>{{ subject }}</b>
                <small>{{ isSubjectSubmitted(subject) ? '已提交' : `${answeredInSubject(subject)}/${questionsInSubject(subject)}` }}</small>
              </span>
            </template>

            <section v-if="!isSubjectSubmitted(subject)" class="quiz-workbench">
              <aside class="knowledge-rail">
                <div class="rail-title">
                  <span>{{ subject }}</span>
                  <strong>{{ groupsBySubject(subject).length }} 个知识点</strong>
                </div>
                <button
                  v-for="group in groupsBySubject(subject)"
                  :key="group.id"
                  :class="{ active: currentGroup.id === group.id, complete: isGroupComplete(group) }"
                  @click="setGroup(group)"
                >
                  <span class="knowledge-index">
                    <el-icon v-if="isGroupComplete(group)"><Check /></el-icon>
                    <template v-else>{{ groupNumberInSubject(group) }}</template>
                  </span>
                  <span>
                    <strong>{{ group.name }}</strong>
                    <small>{{ answeredInGroup(group) }}/{{ group.questions.length }} 已答</small>
                  </span>
                </button>
              </aside>

              <section class="question-panel">
                <div class="knowledge-heading">
                  <div>
                    <span>{{ currentGroup.subject }} · 知识点 {{ groupNumberInSubject(currentGroup) }}/{{ currentSubjectGroups.length }}</span>
                    <h3>{{ currentGroup.name }}</h3>
                    <p>{{ currentGroup.description }}</p>
                  </div>
                  <el-tag effect="plain">{{ currentGroup.questions.length }} 题</el-tag>
                </div>

                <div class="question-list">
                  <article v-for="(question, questionIndex) in currentGroup.questions" :key="question.id" class="question-card">
                    <div class="question-number">{{ String(questionIndex + 1).padStart(2, '0') }}</div>
                    <div class="question-content">
                      <h4>{{ question.stem }}</h4>
                      <el-radio-group v-model="answers[question.id]" class="option-list" :disabled="isSubjectSubmitted(currentGroup.subject)">
                        <el-radio v-for="(option, optionIndex) in question.options" :key="option" :value="optionLetters[optionIndex]" border>
                          <span class="option-letter">{{ optionLetters[optionIndex] }}</span>{{ option }}
                        </el-radio>
                      </el-radio-group>
                    </div>
                  </article>
                </div>

                <div class="quiz-actions">
                  <el-button :disabled="isFirstGroupInSubject" @click="goPrevious">
                    <el-icon><ArrowLeft /></el-icon>上一个
                  </el-button>
                  <span v-if="isSubjectSubmitted(activeSubject)" class="group-done"><el-icon><CircleCheck /></el-icon>{{ activeSubject }}已提交，可继续其他科目</span>
                  <span v-else-if="!isGroupComplete(currentGroup)">还剩 {{ currentGroup.questions.length - answeredInGroup(currentGroup) }} 题</span>
                  <span v-else class="group-done"><el-icon><CircleCheck /></el-icon>当前知识点已答完</span>
                  <el-button v-if="!isLastGroupInSubject" type="primary" plain @click="goNext">
                    下一个<el-icon class="el-icon--right"><ArrowRight /></el-icon>
                  </el-button>
                  <el-button type="primary" :disabled="!canSubmitSubject(activeSubject) || isSubjectSubmitted(activeSubject)" @click="submitSubject(activeSubject)">
                    {{ isSubjectSubmitted(activeSubject) ? '本科目已提交' : `提交${activeSubject}` }}
                  </el-button>
                </div>
              </section>
            </section>

            <section v-else class="subject-report-panel">
              <el-card shadow="never" class="result-card subject-score-card">
                <template #header>
                  <div class="card-heading">
                    <div><span class="section-kicker">分科结果</span><h3>{{ subject }}基础预估</h3></div>
                    <div class="card-actions">
                      <span>已提交 · 折算至 150 分</span>
                      <el-button size="small" plain @click="resetSubject(subject)"><el-icon><Refresh /></el-icon>重新测试本科</el-button>
                    </div>
                  </div>
                </template>
                <div class="single-subject-score">
                  <strong>{{ store.diagnostic.subjectScores[subject] || 0 }}</strong>
                  <span>/ 150 分</span>
                </div>
                <el-progress :percentage="subjectScorePercent(subject)" :stroke-width="11" :show-text="false" />
                <div class="score-facts">
                  <span><small>答对题数</small><b>{{ subjectCorrectCount(subject) }}/{{ subjectQuestionCount(subject) }}</b></span>
                  <span><small>掌握度</small><b>{{ subjectMastery(subject) }}%</b></span>
                  <span><small>薄弱项</small><b>{{ subjectWeakest(subject) }}</b></span>
                </div>
              </el-card>

              <section class="subject-report-grid">
                <el-card shadow="never" class="result-card">
                  <template #header>
                    <div class="card-heading">
                      <div><span class="section-kicker">知识点结果</span><h3>掌握度明细</h3></div>
                      <span>低于 60% 优先复习</span>
                    </div>
                  </template>
                  <div class="knowledge-results result-knowledge-nav">
                    <button v-for="item in knowledgeDetailsBySubject(subject)" :key="item.id" :class="{ active: activeResultGroup(subject)?.id === item.id }" @click="setResultGroup(subject, item.id)">
                      <span :class="masteryClass(item.mastery)">{{ item.mastery }}%</span>
                      <div><strong>{{ item.name }}</strong><small>{{ item.subject }} · 答对 {{ item.correct }}/{{ item.total }}</small></div>
                      <el-tag :type="item.mastery >= 60 ? 'success' : 'warning'" size="small">{{ item.mastery >= 60 ? '基础可用' : '优先补强' }}</el-tag>
                    </button>
                  </div>
                </el-card>

                <el-card shadow="never" class="result-card answer-review-card">
                  <template #header>
                    <div class="card-heading">
                      <div><span class="section-kicker">自动校对</span><h3>{{ activeResultGroup(subject)?.name || subject }}逐题答案核对</h3></div>
                      <span>{{ activeResultGroup(subject)?.correct || 0 }}/{{ activeResultGroup(subject)?.total || 0 }} 答对</span>
                    </div>
                  </template>
                  <div class="answer-review-list">
                    <article v-for="item in answerDetailsByGroup(subject)" :key="item.id" :class="['answer-review-item', item.correct ? 'is-correct' : 'is-wrong']">
                      <div class="answer-review-status">
                        <el-icon v-if="item.correct"><CircleCheck /></el-icon>
                        <el-icon v-else><Close /></el-icon>
                      </div>
                      <div class="answer-review-content">
                        <div class="answer-review-meta"><el-tag size="small" effect="light">{{ item.subject }}</el-tag><span>{{ item.groupName }}</span></div>
                        <h4>{{ item.stem }}</h4>
                        <div class="answer-review-options">
                          <span v-for="option in item.options" :key="option.letter" :class="{ active: option.letter === item.userAnswer, correct: option.letter === item.correctAnswer }">
                            <b>{{ option.letter }}</b>{{ option.text }}
                          </span>
                        </div>
                        <p>你的答案：<strong :class="{ wrong: !item.correct }">{{ item.userAnswer || '未作答' }}</strong><i>正确答案：{{ item.correctAnswer }}</i></p>
                      </div>
                    </article>
                  </div>
                </el-card>
              </section>
            </section>
          </el-tab-pane>
        </el-tabs>
      </section>
    </template>

    <template v-else>
      <section class="result-hero">
        <div class="result-score"><span>基础诊断预估</span><strong>{{ store.currentScore }}</strong><small>/ 450 分</small></div>
        <div class="result-metrics">
          <div><small>答对题数</small><strong>{{ store.diagnostic.correctCount }}/{{ store.diagnostic.totalQuestions }}</strong></div>
          <div><small>整体掌握度</small><strong>{{ store.diagnostic.knowledge }}%</strong></div>
          <div><small>平均答题速度</small><strong>{{ averageSeconds }} 秒/题</strong></div>
          <div><small>需要优先补强</small><strong>{{ store.diagnostic.mistakeType }}</strong></div>
        </div>
      </section>

      <section class="result-tabs-card">
        <el-tabs v-model="activeResultSubject" class="result-subject-tabs">
          <el-tab-pane v-for="subject in subjects" :key="subject" :name="subject">
            <template #label>
              <span class="subject-tab-label">
                <b>{{ subject }}</b>
                <small>{{ subjectCorrectCount(subject) }}/{{ subjectQuestionCount(subject) }}</small>
              </span>
            </template>

            <section class="subject-report-panel">
              <el-card shadow="never" class="result-card subject-score-card">
                <template #header>
                  <div class="card-heading">
                    <div><span class="section-kicker">分科结果</span><h3>{{ subject }}基础预估</h3></div>
                    <div class="card-actions">
                      <span>折算至 150 分</span>
                      <el-button size="small" plain @click="resetSubject(subject)"><el-icon><Refresh /></el-icon>重新测试本科</el-button>
                    </div>
                  </div>
                </template>
                <div class="single-subject-score">
                  <strong>{{ store.diagnostic.subjectScores[subject] || 0 }}</strong>
                  <span>/ 150 分</span>
                </div>
                <el-progress :percentage="subjectScorePercent(subject)" :stroke-width="11" :show-text="false" />
                <div class="score-facts">
                  <span><small>答对题数</small><b>{{ subjectCorrectCount(subject) }}/{{ subjectQuestionCount(subject) }}</b></span>
                  <span><small>掌握度</small><b>{{ subjectMastery(subject) }}%</b></span>
                  <span><small>薄弱项</small><b>{{ subjectWeakest(subject) }}</b></span>
                </div>
              </el-card>

              <section class="subject-report-grid">
                <el-card shadow="never" class="result-card">
                  <template #header>
                    <div class="card-heading">
                      <div><span class="section-kicker">知识点结果</span><h3>掌握度明细</h3></div>
                      <span>低于 60% 优先复习</span>
                    </div>
                  </template>
                  <div class="knowledge-results result-knowledge-nav">
                    <button v-for="item in knowledgeDetailsBySubject(subject)" :key="item.id" :class="{ active: activeResultGroup(subject)?.id === item.id }" @click="setResultGroup(subject, item.id)">
                      <span :class="masteryClass(item.mastery)">{{ item.mastery }}%</span>
                      <div><strong>{{ item.name }}</strong><small>{{ item.subject }} · 答对 {{ item.correct }}/{{ item.total }}</small></div>
                      <el-tag :type="item.mastery >= 60 ? 'success' : 'warning'" size="small">{{ item.mastery >= 60 ? '基础可用' : '优先补强' }}</el-tag>
                    </button>
                  </div>
                </el-card>

                <el-card shadow="never" class="result-card answer-review-card">
                  <template #header>
                    <div class="card-heading">
                      <div><span class="section-kicker">自动校对</span><h3>{{ activeResultGroup(subject)?.name || subject }}逐题答案核对</h3></div>
                      <span>{{ activeResultGroup(subject)?.correct || 0 }}/{{ activeResultGroup(subject)?.total || 0 }} 答对</span>
                    </div>
                  </template>
                  <div class="answer-review-list">
                    <article v-for="item in answerDetailsByGroup(subject)" :key="item.id" :class="['answer-review-item', item.correct ? 'is-correct' : 'is-wrong']">
                      <div class="answer-review-status">
                        <el-icon v-if="item.correct"><CircleCheck /></el-icon>
                        <el-icon v-else><Close /></el-icon>
                      </div>
                      <div class="answer-review-content">
                        <div class="answer-review-meta"><el-tag size="small" effect="light">{{ item.subject }}</el-tag><span>{{ item.groupName }}</span></div>
                        <h4>{{ item.stem }}</h4>
                        <div class="answer-review-options">
                          <span v-for="option in item.options" :key="option.letter" :class="{ active: option.letter === item.userAnswer, correct: option.letter === item.correctAnswer }">
                            <b>{{ option.letter }}</b>{{ option.text }}
                          </span>
                        </div>
                        <p>你的答案：<strong :class="{ wrong: !item.correct }">{{ item.userAnswer || '未作答' }}</strong><i>正确答案：{{ item.correctAnswer }}</i></p>
                      </div>
                    </article>
                  </div>
                </el-card>
              </section>
            </section>
          </el-tab-pane>
        </el-tabs>
      </section>

      <div class="result-actions">
        <el-button size="large" @click="restart"><el-icon><Refresh /></el-icon>重新诊断</el-button>
        <el-button type="primary" size="large" @click="router.push('/target')">查看目标分与差距<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { fetchDiagnosticGroups } from '../data/diagnostic-questions'
import { useApplicationStore } from '../stores/application'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const store = useApplicationStore()
const auth = useAuthStore()
const subjects = computed(() => store.selectedMajor?.subjects || [])
const groups = ref([])

async function loadGroups() {
  groups.value = await fetchDiagnosticGroups(subjects.value)
}
onMounted(loadGroups)
watch(subjects, loadGroups)
const activeSubject = ref(subjects.value[0] || '政治')
const activeResultSubject = ref(subjects.value[0] || '政治')
const activeGroupId = ref('')
const activeResultGroupIds = reactive({})
const answers = reactive({ ...(store.diagnostic.completed ? {} : store.diagnostic.answers) })
const optionLetters = ['A', 'B', 'C', 'D']
const startedAt = Date.now()
const elapsedSeconds = ref(0)
const timer = window.setInterval(() => { elapsedSeconds.value = Math.round((Date.now() - startedAt) / 1000) }, 1000)
onBeforeUnmount(() => window.clearInterval(timer))

const allQuestions = computed(() => groups.value.flatMap(group => group.questions))
const totalQuestions = computed(() => allQuestions.value.length)
const answeredCount = computed(() => allQuestions.value.filter(question => answers[question.id] !== undefined).length)
const progressPercent = computed(() => Math.round(answeredCount.value / Math.max(totalQuestions.value, 1) * 100))
const averageSeconds = computed(() => Math.round(store.diagnostic.durationSeconds / Math.max(store.diagnostic.totalQuestions, 1)))
const currentGroup = computed(() => {
  const subject = activeSubject.value || subjects.value[0]
  return groups.value.find(group => group.id === activeGroupId.value)
    || groups.value.find(group => group.subject === subject)
    || groups.value[0]
    || { questions: [] }
})
const currentSubjectGroups = computed(() => groups.value.filter(group => group.subject === currentGroup.value.subject))
const currentIndexInSubject = computed(() => currentSubjectGroups.value.findIndex(group => group.id === currentGroup.value.id))
const isFirstGroupInSubject = computed(() => currentIndexInSubject.value <= 0)
const isLastGroupInSubject = computed(() => currentIndexInSubject.value >= currentSubjectGroups.value.length - 1)

function groupsBySubject(subject) { return groups.value.filter(group => group.subject === subject) }
function answeredInGroup(group) { return group.questions.filter(question => answers[question.id] !== undefined).length }
function isGroupComplete(group) { return answeredInGroup(group) === group.questions.length }
function questionsInSubject(subject) { return groupsBySubject(subject).reduce((sum, group) => sum + group.questions.length, 0) }
function answeredInSubject(subject) { return groupsBySubject(subject).flatMap(group => group.questions).filter(question => answers[question.id] !== undefined).length }
function isSubjectSubmitted(subject) { return (store.diagnostic.submittedSubjects || []).includes(subject) }
function canSubmitSubject(subject) { return answeredInSubject(subject) === questionsInSubject(subject) && questionsInSubject(subject) > 0 }
function groupNumberInSubject(group) { return Math.max(1, groupsBySubject(group.subject).findIndex(item => item.id === group.id) + 1) }
function formatTime(seconds) { return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}` }
function masteryClass(mastery) { return mastery >= 80 ? 'strong' : mastery >= 60 ? 'medium' : 'weak' }
function knowledgeDetailsBySubject(subject) { return (store.diagnostic.knowledgeDetails || []).filter(item => item.subject === subject) }
function answerDetailsBySubject(subject) { return (store.diagnostic.answerDetails || []).filter(item => item.subject === subject) }
function activeResultGroup(subject) {
  const details = knowledgeDetailsBySubject(subject)
  return details.find(item => item.id === activeResultGroupIds[subject]) || details[0] || null
}
function setResultGroup(subject, groupId) {
  activeResultGroupIds[subject] = groupId
}
function answerDetailsByGroup(subject) {
  const group = activeResultGroup(subject)
  if (!group) return []
  return answerDetailsBySubject(subject).filter(item => item.groupName === group.name)
}
function subjectQuestionCount(subject) { return answerDetailsBySubject(subject).length || questionsInSubject(subject) }
function subjectCorrectCount(subject) { return answerDetailsBySubject(subject).filter(item => item.correct).length }
function subjectScorePercent(subject) { return Math.round((store.diagnostic.subjectScores[subject] || 0) / 150 * 100) }
function subjectMastery(subject) {
  const total = subjectQuestionCount(subject)
  return total ? Math.round(subjectCorrectCount(subject) / total * 100) : 0
}
function subjectWeakest(subject) {
  const details = knowledgeDetailsBySubject(subject)
  if (!details.length) return '暂无'
  return [...details].sort((a, b) => a.mastery - b.mastery)[0].name
}

function setGroup(group) {
  activeSubject.value = group.subject
  activeGroupId.value = group.id
}

function handleSubjectChange(subject) {
  const firstGroup = groupsBySubject(subject)[0]
  if (firstGroup) activeGroupId.value = firstGroup.id
}

function goPrevious() {
  const previous = currentSubjectGroups.value[currentIndexInSubject.value - 1]
  if (previous) setGroup(previous)
}

function goNext() {
  if (!isGroupComplete(currentGroup.value)) {
    ElMessage.warning('请先完成当前知识点的全部题目')
    return
  }
  const next = currentSubjectGroups.value[currentIndexInSubject.value + 1]
  if (next) setGroup(next)
}

function submitSubject(subject, { silent = false } = {}) {
  if (isSubjectSubmitted(subject)) return
  if (!canSubmitSubject(subject)) {
    ElMessage.warning(`请先完成${subject}的全部题目`)
    return
  }

  const subjectGroups = groupsBySubject(subject)
  const subjectQuestions = subjectGroups.flatMap(group => group.questions)
  const subjectKnowledgeDetails = subjectGroups.map(group => {
    const correct = group.questions.filter(question => answers[question.id] === question.answer).length
    return { id: group.id, name: group.name, subject: group.subject, correct, total: group.questions.length, mastery: Math.round(correct / group.questions.length * 100) }
  })
  const subjectAnswerDetails = subjectGroups.flatMap(group => group.questions.map(question => ({
    id: question.id,
    subject: group.subject,
    groupName: group.name,
    stem: question.stem,
    options: question.options.map((option, index) => ({ letter: optionLetters[index], text: option })),
    userAnswer: answers[question.id],
    correctAnswer: question.answer,
    correct: answers[question.id] === question.answer
  })))
  const submittedSubjects = Array.from(new Set([...(store.diagnostic.submittedSubjects || []), subject]))
  const knowledgeDetails = [
    ...(store.diagnostic.knowledgeDetails || []).filter(item => item.subject !== subject),
    ...subjectKnowledgeDetails
  ]
  const answerDetails = [
    ...(store.diagnostic.answerDetails || []).filter(item => item.subject !== subject),
    ...subjectAnswerDetails
  ]
  const subjectCorrect = subjectQuestions.filter(question => answers[question.id] === question.answer).length
  const subjectScores = {
    ...store.diagnostic.subjectScores,
    [subject]: Math.round(subjectCorrect / subjectQuestions.length * 150)
  }
  const correctCount = answerDetails.filter(item => item.correct).length
  const submittedQuestionTotal = answerDetails.length
  const durationSeconds = Math.max(elapsedSeconds.value, submittedQuestionTotal * 8)
  const secondsPerQuestion = durationSeconds / Math.max(submittedQuestionTotal, 1)
  const speed = Math.round(Math.max(20, Math.min(100, 100 - Math.max(0, secondsPerQuestion - 35) * 1.4)))
  const weakest = [...knowledgeDetails].sort((a, b) => a.mastery - b.mastery)[0]
  const completed = submittedSubjects.length === subjects.value.length

  store.completeDiagnostic({
    answers: { ...answers },
    submittedSubjects,
    subjectScores,
    knowledge: Math.round(correctCount / Math.max(submittedQuestionTotal, 1) * 100),
    speed,
    mistakeType: weakest ? weakest.name : '暂无明显薄弱项',
    weeklyHours: store.weeklyHours,
    knowledgeDetails,
    answerDetails,
    correctCount,
    totalQuestions: submittedQuestionTotal,
    durationSeconds
  }, completed)

  if (completed) {
    window.clearInterval(timer)
    activeResultSubject.value = subject
    activeResultGroupIds[subject] = subjectKnowledgeDetails[0]?.id || ''
    window.scrollTo({ top: 0, behavior: 'smooth' })
    if (!silent) ElMessage.success('全部科目已提交，已生成完整诊断报告')
  } else {
    activeSubject.value = subject
    activeResultGroupIds[subject] = subjectKnowledgeDetails[0]?.id || ''
    if (!silent) ElMessage.success(`${subject}已提交，已生成本科目报告`)
  }
}

// 管理员测试用：给所有题目随机选答案，并依次提交各科目，直接生成完整诊断报告。
function adminAutofill() {
  if (!groups.value.length) {
    ElMessage.warning('题目尚未加载完成，请稍候再试')
    return
  }
  groups.value.forEach(group => {
    group.questions.forEach(question => {
      answers[question.id] = optionLetters[Math.floor(Math.random() * question.options.length)]
    })
  })
  subjects.value.forEach(subject => {
    if (!isSubjectSubmitted(subject)) submitSubject(subject, { silent: true })
  })
  ElMessage.success('已随机填充并提交全部科目，已生成诊断报告')
}

function resetSubject(subject) {  const subjectGroups = groupsBySubject(subject)
  const subjectQuestionIds = new Set(subjectGroups.flatMap(group => group.questions.map(question => question.id)))
  subjectQuestionIds.forEach(id => delete answers[id])

  const submittedSubjects = (store.diagnostic.submittedSubjects || []).filter(item => item !== subject)
  const knowledgeDetails = (store.diagnostic.knowledgeDetails || []).filter(item => item.subject !== subject)
  const answerDetails = (store.diagnostic.answerDetails || []).filter(item => item.subject !== subject)
  const subjectScores = { ...store.diagnostic.subjectScores, [subject]: 0 }
  const correctCount = answerDetails.filter(item => item.correct).length
  const total = answerDetails.length
  const weakest = [...knowledgeDetails].sort((a, b) => a.mastery - b.mastery)[0]

  store.completeDiagnostic({
    answers: Object.fromEntries(Object.entries(store.diagnostic.answers || {}).filter(([id]) => !subjectQuestionIds.has(id))),
    submittedSubjects,
    subjectScores,
    knowledge: total ? Math.round(correctCount / total * 100) : 0,
    mistakeType: weakest ? weakest.name : '暂无明显薄弱项',
    knowledgeDetails,
    answerDetails,
    correctCount,
    totalQuestions: total,
    durationSeconds: store.diagnostic.durationSeconds
  }, false)

  activeSubject.value = subject
  activeResultSubject.value = subject
  delete activeResultGroupIds[subject]
  activeGroupId.value = subjectGroups[0]?.id || ''
  ElMessage.success(`${subject}已重置，可以重新测试`)
}

async function restart() {
  let resetPlan = false
  if (store.hasLearningProgress) {
    try {
      await ElMessageBox.confirm(
        '重新诊断会更新基础分与薄弱项。\n\n「只更新基线」：保留当前阶段、复习队列与历史测试，任务按新诊断重排。\n「诊断并重排计划」：阶段回到 1，清空测试与复习记录。',
        '重新诊断',
        {
          distinguishCancelAndClose: true,
          confirmButtonText: '只更新基线',
          cancelButtonText: '诊断并重排计划',
          type: 'warning',
        }
      )
      resetPlan = false
    } catch (action) {
      if (action === 'cancel') {
        resetPlan = true
      } else {
        return
      }
    }
  }

  store.resetDiagnostic({ resetPlan })
  Object.keys(answers).forEach(key => delete answers[key])
  Object.keys(activeResultGroupIds).forEach(key => delete activeResultGroupIds[key])
  activeSubject.value = subjects.value[0] || '政治'
  activeResultSubject.value = subjects.value[0] || '政治'
  activeGroupId.value = groups.value.find(g => g.subject === activeSubject.value)?.id || ''
  elapsedSeconds.value = 0
  ElMessage.success(resetPlan ? '已重置诊断与学习进度，请重新作答' : '已重置诊断基线，请重新作答')
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<style scoped lang="less" src="../styles/views/Diagnosis.less"></style>
