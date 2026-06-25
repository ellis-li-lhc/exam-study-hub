<template>
  <div class="diagnosis-page page-stack">
    <section class="page-intro">
      <div>
        <span class="section-kicker">STEP 03</span>
        <h2>{{ store.diagnosisComplete ? '基础诊断报告' : '知识点基础诊断' }}</h2>
        <p>{{ store.diagnosisComplete ? '分数完全由答题结果生成，可随时重新测试。' : `共 ${groups.length} 个知识点、${totalQuestions} 道单选题，每个知识点 3~5 道。` }}</p>
      </div>
      <el-tag :type="store.diagnosisComplete ? 'success' : 'primary'" effect="light">
        {{ store.diagnosisComplete ? '诊断完成' : formatTime(elapsedSeconds) }}
      </el-tag>
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
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { getDiagnosticGroups } from '../data/diagnostic-questions'
import { useApplicationStore } from '../stores/application'

const router = useRouter()
const store = useApplicationStore()
const subjects = computed(() => store.selectedMajor?.subjects || [])
const groups = computed(() => getDiagnosticGroups(subjects.value))
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

function submitSubject(subject) {
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
    ElMessage.success('全部科目已提交，已生成完整诊断报告')
  } else {
    activeSubject.value = subject
    activeResultGroupIds[subject] = subjectKnowledgeDetails[0]?.id || ''
    ElMessage.success(`${subject}已提交，已生成本科目报告`)
  }
}

function resetSubject(subject) {
  const subjectGroups = groupsBySubject(subject)
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

function restart() {
  store.resetDiagnostic()
  Object.keys(answers).forEach(key => delete answers[key])
  activeSubject.value = subjects.value[0] || '政治'
  activeResultSubject.value = subjects.value[0] || '政治'
  activeGroupId.value = ''
  window.location.reload()
}
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:14px}
.page-intro{display:flex;align-items:flex-start;justify-content:space-between}
.page-intro h2{color:var(--ink);font-size:1.55rem}
.page-intro p{margin-top:4px;color:var(--text-secondary);font-size:.82rem}
.section-kicker{display:block;margin-bottom:4px;color:var(--primary);font-size:.7rem;font-weight:800;letter-spacing:.1em}
.diagnosis-shell{overflow:hidden;border:1px solid var(--line);border-radius:18px;background:#fff;box-shadow:0 12px 30px rgba(30,64,120,.045)}
.diagnosis-summary{display:grid;grid-template-columns:128px 1fr;align-items:center;gap:16px;padding:14px 18px;background:linear-gradient(135deg,#f8fbff,#eef5ff);border-bottom:1px solid var(--line)}
.diagnosis-summary>div{display:flex;justify-content:space-between}
.diagnosis-summary span,.diagnosis-summary small{color:var(--text-muted);font-size:.7rem}
.diagnosis-summary strong{color:var(--ink);font-size:1rem}
.diagnosis-summary small{grid-column:1/-1;margin-top:-8px}
.subject-tabs{padding:0 18px 18px}
:deep(.subject-tabs .el-tabs__header){position:sticky;top:80px;z-index:5;margin:0 -18px 12px;padding:0 18px;background:#fff;border-bottom:1px solid var(--line)}
:deep(.subject-tabs .el-tabs__nav-wrap:after){display:none}
:deep(.subject-tabs .el-tabs__item){height:52px;padding:0 18px}
.subject-tab-label{display:flex;align-items:center;gap:8px}
.subject-tab-label b{font-size:.84rem}
.subject-tab-label small{padding:2px 7px;border-radius:999px;color:var(--text-muted);font-size:.64rem;background:#f0f4fa}
:deep(.subject-tabs .is-active .subject-tab-label small){color:var(--primary);background:var(--primary-soft)}
.quiz-workbench{display:grid;grid-template-columns:248px minmax(0,1fr);gap:14px;align-items:stretch}
.knowledge-rail{height:100%;box-sizing:border-box;padding:10px;border:1px solid #dce6f4;border-radius:16px;background:#f8fbff}
.rail-title{display:flex;align-items:center;justify-content:space-between;padding:4px 6px 10px}
.rail-title span{color:var(--primary);font-size:.72rem;font-weight:800}
.rail-title strong{color:var(--text-muted);font-size:.66rem}
.knowledge-rail button{width:100%;display:flex;align-items:center;gap:9px;margin-bottom:7px;padding:9px;border:1px solid transparent;border-radius:12px;text-align:left;background:#fff;cursor:pointer;transition:.18s ease}
.knowledge-rail button:hover{border-color:#bfd4ff;background:#fafdff}
.knowledge-rail button.active{border-color:#7aa7f7;background:#edf5ff;box-shadow:0 6px 16px rgba(37,99,235,.09)}
.knowledge-rail button.complete:not(.active){border-color:#c9efdf;background:#f6fffb}
.knowledge-index{width:28px;height:28px;display:grid;place-items:center;flex:0 0 auto;border-radius:9px;color:var(--text-muted);font-size:.68rem;font-weight:900;background:#edf1f6}
.knowledge-rail button.active .knowledge-index{color:#fff;background:var(--primary)}
.knowledge-rail button.complete:not(.active) .knowledge-index{color:#fff;background:var(--mint)}
.knowledge-rail strong,.knowledge-rail small{display:block}
.knowledge-rail strong{max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--ink);font-size:.76rem}
.knowledge-rail small{margin-top:1px;color:var(--text-muted);font-size:.64rem}
.question-panel{min-width:0;display:flex;flex-direction:column;border:1px solid #dce6f4;border-radius:16px;background:#fff;overflow:hidden}
.knowledge-heading{display:flex;align-items:flex-start;justify-content:space-between;padding:16px 18px;background:linear-gradient(135deg,#f8fbff,#edf4ff)}
.knowledge-heading span,.knowledge-heading p{color:var(--text-muted);font-size:.7rem}
.knowledge-heading h3{margin:2px 0;color:var(--ink);font-size:1.1rem}
.question-list{display:grid;flex:1}
.question-card{display:flex;gap:12px;padding:18px;border-top:1px solid var(--line);background:#fff}
.question-number{width:32px;height:32px;display:grid;place-items:center;flex:0 0 auto;border-radius:9px;color:var(--primary);font-size:.7rem;font-weight:900;background:var(--primary-soft)}
.question-content{flex:1;min-width:0}
.question-content h4{margin:3px 0 12px;color:var(--ink);font-size:.9rem;line-height:1.45}
.option-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;width:100%}
:deep(.option-list .el-radio){width:100%;height:auto;min-height:40px;margin:0;padding:9px 11px;border-radius:10px}
:deep(.option-list .el-radio__label){white-space:normal;line-height:1.35;font-size:.78rem}
.option-letter{display:inline-grid;place-items:center;width:21px;height:21px;margin-right:7px;border-radius:6px;color:var(--text-secondary);font-size:.66rem;background:#eef2f7}
.quiz-actions{margin-top:auto;position:sticky;bottom:0;z-index:4;display:flex;align-items:center;gap:10px;padding:12px 16px;border-top:1px solid var(--line);background:rgba(255,255,255,.95);backdrop-filter:blur(10px)}
.quiz-actions>span{flex:1;text-align:center;color:var(--text-muted);font-size:.7rem}
.quiz-actions .group-done{display:flex;justify-content:center;align-items:center;gap:5px;color:var(--mint)}
.result-hero{display:grid;grid-template-columns:190px 1fr;gap:24px;align-items:center;padding:28px;border-radius:22px;color:#dce8f9;background:linear-gradient(135deg,#14233e,#234875)}
.result-score{padding-right:24px;border-right:1px solid rgba(255,255,255,.15)}
.result-score span,.result-score small{color:#9fb5d3;font-size:.72rem}
.result-score strong{display:inline-block;margin:0 7px;color:#fff;font-size:3rem}
.result-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.result-metrics div{padding:13px;border-radius:12px;background:rgba(255,255,255,.07)}
.result-metrics small,.result-metrics strong{display:block}
.result-metrics small{color:#9fb5d3;font-size:.65rem}
.result-metrics strong{margin-top:4px;color:#fff;font-size:.85rem}
.result-tabs-card{border:1px solid var(--line);border-radius:20px;background:#fff;overflow:hidden}
.result-subject-tabs{padding:0 18px 18px}
:deep(.result-subject-tabs .el-tabs__header){margin:0 -18px 16px;padding:0 18px;background:#fff;border-bottom:1px solid var(--line)}
:deep(.result-subject-tabs .el-tabs__nav-wrap:after){display:none}
:deep(.result-subject-tabs .el-tabs__item){height:54px;padding:0 18px}
.subject-report-panel{display:flex;flex-direction:column;gap:16px}
.subject-report-grid{display:grid;grid-template-columns:340px minmax(0,1fr);gap:14px;align-items:start}
.result-grid{display:grid;grid-template-columns:.82fr 1.18fr;gap:16px;align-items:start;margin-bottom:16px}
.result-card{border-radius:19px;border-color:var(--line)}
.card-heading{display:flex;align-items:center;justify-content:space-between}
.card-heading h3{color:var(--ink)}
.card-heading>span{color:var(--text-muted);font-size:.7rem}
.card-actions{display:flex;align-items:center;gap:10px}
.card-actions>span{color:var(--text-muted);font-size:.7rem}
.subject-results{display:flex;flex-direction:column;gap:18px}
.subject-results>div>div{display:flex;justify-content:space-between;margin-bottom:7px}
.subject-results strong{color:var(--ink);font-size:.8rem}
.subject-results b{color:var(--primary);font-size:.82rem}
.subject-score-card :deep(.el-card__body){display:flex;flex-direction:column;gap:14px}
.single-subject-score{display:flex;align-items:baseline;gap:7px;padding:16px;border-radius:15px;background:linear-gradient(135deg,#f5f9ff,#edf4ff)}
.single-subject-score strong{color:var(--primary);font-size:2.2rem;line-height:1}
.single-subject-score span{color:var(--text-muted);font-size:.8rem}
.score-facts{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.score-facts span{padding:11px;border-radius:12px;background:#f7f9fc}
.score-facts small,.score-facts b{display:block}
.score-facts small{color:var(--text-muted);font-size:.65rem}
.score-facts b{margin-top:3px;color:var(--ink);font-size:.78rem;line-height:1.35}
.knowledge-results{display:flex;flex-direction:column;gap:7px}
.knowledge-results button{width:100%;display:flex;align-items:center;gap:9px;padding:9px;border:1px solid transparent;border-radius:11px;text-align:left;background:#f6f8fc;cursor:pointer;transition:.18s ease}
.knowledge-results button:hover{border-color:#bfd4ff;background:#fafdff}
.knowledge-results button.active{border-color:#7aa7f7;background:#edf5ff;box-shadow:0 6px 16px rgba(37,99,235,.08)}
.knowledge-results button>span{width:38px;height:38px;display:grid;place-items:center;flex:0 0 auto;border-radius:10px;font-size:.68rem;font-weight:900}
.knowledge-results button>span.strong{color:#08765a;background:#ddf6ed}
.knowledge-results button>span.medium{color:#2867d8;background:#e5efff}
.knowledge-results button>span.weak{color:#b06b00;background:#fff0ce}
.knowledge-results button>div{flex:1}
.knowledge-results strong,.knowledge-results small{display:block}
.knowledge-results strong{max-width:170px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--ink);font-size:.76rem}
.knowledge-results small{color:var(--text-muted);font-size:.65rem}
.knowledge-results :deep(.el-tag){height:28px;padding:0 8px;border-radius:10px;font-size:.68rem}
.answer-review-card{overflow:hidden}
.answer-review-list{display:grid;gap:12px}
.answer-review-item{display:flex;gap:12px;padding:14px;border:1px solid #e4eaf3;border-radius:14px;background:#fff}
.answer-review-item.is-correct{border-color:#bcebdc;background:#f8fffc}
.answer-review-item.is-wrong{border-color:#ffd9a8;background:#fffaf1}
.answer-review-status{width:30px;height:30px;display:grid;place-items:center;flex:0 0 auto;border-radius:10px;color:#fff;background:var(--mint)}
.answer-review-item.is-wrong .answer-review-status{background:#f59e0b}
.answer-review-content{min-width:0;flex:1}
.answer-review-meta{display:flex;align-items:center;gap:8px;margin-bottom:8px;color:var(--text-muted);font-size:.7rem}
.answer-review-content h4{margin:0 0 10px;color:var(--ink);font-size:.88rem;line-height:1.55}
.answer-review-options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.answer-review-options span{display:flex;gap:7px;align-items:flex-start;padding:9px 10px;border:1px solid #e6ebf3;border-radius:10px;color:var(--text-secondary);font-size:.75rem;background:#fff}
.answer-review-options b{display:grid;place-items:center;width:22px;height:22px;flex:0 0 auto;border-radius:7px;background:#eef2f7}
.answer-review-options span.active{border-color:#f59e0b;background:#fff7e8}
.answer-review-options span.correct{border-color:#18b782;background:#ecfff7}
.answer-review-content p{display:flex;gap:16px;margin:10px 0 0;color:var(--text-muted);font-size:.74rem}
.answer-review-content strong{color:#08765a}
.answer-review-content strong.wrong{color:#b45309}
.answer-review-content i{font-style:normal;color:var(--ink)}
.result-actions{display:flex;justify-content:flex-end;gap:12px}
@media(max-width:1180px){.quiz-workbench{grid-template-columns:220px minmax(0,1fr)}.knowledge-rail strong{max-width:132px}.option-list{grid-template-columns:1fr}}
@media(max-width:900px){.quiz-workbench{grid-template-columns:1fr}.knowledge-rail{position:static}.result-hero{grid-template-columns:1fr}.result-score{border-right:0;border-bottom:1px solid rgba(255,255,255,.15);padding:0 0 18px}.result-grid,.subject-report-grid{grid-template-columns:1fr}}
@media(max-width:700px){.page-intro{gap:12px;flex-direction:column}.diagnosis-summary{grid-template-columns:1fr}.diagnosis-summary small{grid-column:auto;margin:0}.subject-tabs{padding:0 12px 14px}:deep(.subject-tabs .el-tabs__header){margin:0 -12px 12px;padding:0 12px;top:0}:deep(.subject-tabs .el-tabs__item){height:48px;padding:0 12px}.option-list,.result-metrics,.answer-review-options,.score-facts{grid-template-columns:1fr}.card-heading{gap:10px;align-items:flex-start;flex-direction:column}.card-actions{align-items:flex-start;flex-direction:column}.quiz-actions{align-items:stretch;flex-direction:column}.quiz-actions>span{order:-1}.question-card{padding:14px 12px}.result-actions{flex-direction:column}.result-actions .el-button{width:100%;margin:0}}
</style>
