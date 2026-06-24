<template>
  <div class="diagnosis-page page-stack">
    <section class="page-intro">
      <div><span class="section-kicker">STEP 03</span><h2>{{ store.diagnosisComplete ? '基础诊断报告' : '知识点基础诊断' }}</h2><p>{{ store.diagnosisComplete ? '分数完全由答题结果生成，可随时重新测试。' : `共 ${groups.length} 个知识点、${totalQuestions} 道单选题，每个知识点 3 道。` }}</p></div>
      <el-tag :type="store.diagnosisComplete ? 'success' : 'primary'" effect="light">{{ store.diagnosisComplete ? '诊断完成' : formatTime(elapsedSeconds) }}</el-tag>
    </section>

    <template v-if="!store.diagnosisComplete">
      <section class="quiz-progress-card">
        <div><span>答题进度</span><strong>{{ answeredCount }} / {{ totalQuestions }}</strong></div>
        <el-progress :percentage="progressPercent" :stroke-width="10" :show-text="false" />
        <small>答错不会影响操作，请按真实基础作答，不确定时也需要选择一个答案。</small>
      </section>

      <section class="quiz-layout">
        <aside class="knowledge-nav">
          <div class="nav-title"><span class="section-kicker">诊断范围</span><h3>考试科目与知识点</h3></div>
          <div v-for="subject in subjects" :key="subject" class="subject-group">
            <strong>{{ subject }}</strong>
            <button v-for="group in groups.filter(item => item.subject === subject)" :key="group.id" :class="{ active: currentGroup.id === group.id, complete: isGroupComplete(group) }" @click="activeGroupIndex = groups.findIndex(item => item.id === group.id)">
              <span><el-icon v-if="isGroupComplete(group)"><Check /></el-icon><template v-else>{{ groups.findIndex(item => item.id === group.id) + 1 }}</template></span>
              <span><b>{{ group.name }}</b><small>{{ answeredInGroup(group) }}/{{ group.questions.length }} 已答</small></span>
            </button>
          </div>
        </aside>

        <section class="question-panel">
          <div class="knowledge-heading">
            <div><span>{{ currentGroup.subject }} · 知识点 {{ activeGroupIndex + 1 }}/{{ groups.length }}</span><h3>{{ currentGroup.name }}</h3><p>{{ currentGroup.description }}</p></div>
            <el-tag effect="plain">{{ currentGroup.questions.length }} 题</el-tag>
          </div>

          <article v-for="(question, questionIndex) in currentGroup.questions" :key="question.id" class="question-card">
            <div class="question-number">{{ String(questionIndex + 1).padStart(2, '0') }}</div>
            <div class="question-content">
              <h4>{{ question.stem }}</h4>
              <el-radio-group v-model="answers[question.id]" class="option-list">
                <el-radio v-for="(option, optionIndex) in question.options" :key="option" :value="optionIndex" border>
                  <span class="option-letter">{{ optionLetters[optionIndex] }}</span>{{ option }}
                </el-radio>
              </el-radio-group>
            </div>
          </article>

          <div class="quiz-actions">
            <el-button :disabled="activeGroupIndex === 0" @click="activeGroupIndex--"><el-icon><ArrowLeft /></el-icon>上一个知识点</el-button>
            <span v-if="!isGroupComplete(currentGroup)">当前知识点还有 {{ currentGroup.questions.length - answeredInGroup(currentGroup) }} 题未答</span>
            <span v-else class="group-done"><el-icon><CircleCheck /></el-icon>当前知识点已答完</span>
            <el-button v-if="activeGroupIndex < groups.length - 1" type="primary" @click="goNext">下一个知识点<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button>
            <el-button v-else type="primary" :disabled="answeredCount < totalQuestions" @click="submitQuiz">提交并生成诊断</el-button>
          </div>
        </section>
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

      <section class="result-grid">
        <el-card shadow="never" class="result-card">
          <template #header><div class="card-heading"><div><span class="section-kicker">分科结果</span><h3>当前基础预估</h3></div><span>每科折算至 150 分</span></div></template>
          <div class="subject-results"><div v-for="subject in subjects" :key="subject"><div><strong>{{ subject }}</strong><b>{{ store.diagnostic.subjectScores[subject] || 0 }} 分</b></div><el-progress :percentage="Math.round((store.diagnostic.subjectScores[subject] || 0) / 150 * 100)" :stroke-width="10" :show-text="false" /></div></div>
        </el-card>

        <el-card shadow="never" class="result-card">
          <template #header><div class="card-heading"><div><span class="section-kicker">知识点结果</span><h3>掌握度明细</h3></div><span>低于 60% 优先复习</span></div></template>
          <div class="knowledge-results"><div v-for="item in store.diagnostic.knowledgeDetails" :key="item.id"><span :class="masteryClass(item.mastery)">{{ item.mastery }}%</span><div><strong>{{ item.name }}</strong><small>{{ item.subject }} · 答对 {{ item.correct }}/{{ item.total }}</small></div><el-tag :type="item.mastery >= 60 ? 'success' : 'warning'" size="small">{{ item.mastery >= 60 ? '基础可用' : '优先补强' }}</el-tag></div></div>
        </el-card>
      </section>

      <div class="result-actions"><el-button @click="restart"><el-icon><Refresh /></el-icon>重新诊断</el-button><el-button type="primary" size="large" @click="router.push('/target')">查看目标分与差距<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button></div>
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
const activeGroupIndex = ref(0)
const answers = reactive({ ...(store.diagnostic.completed ? {} : store.diagnostic.answers) })
const optionLetters = ['A', 'B', 'C', 'D']
const startedAt = Date.now()
const elapsedSeconds = ref(0)
const timer = window.setInterval(() => { elapsedSeconds.value = Math.round((Date.now() - startedAt) / 1000) }, 1000)
onBeforeUnmount(() => window.clearInterval(timer))

const currentGroup = computed(() => groups.value[activeGroupIndex.value] || { questions: [] })
const allQuestions = computed(() => groups.value.flatMap(group => group.questions))
const totalQuestions = computed(() => allQuestions.value.length)
const answeredCount = computed(() => allQuestions.value.filter(question => answers[question.id] !== undefined).length)
const progressPercent = computed(() => Math.round(answeredCount.value / Math.max(totalQuestions.value, 1) * 100))
const averageSeconds = computed(() => Math.round(store.diagnostic.durationSeconds / Math.max(store.diagnostic.totalQuestions, 1)))

function answeredInGroup(group) { return group.questions.filter(question => answers[question.id] !== undefined).length }
function isGroupComplete(group) { return answeredInGroup(group) === group.questions.length }
function formatTime(seconds) { return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}` }
function masteryClass(mastery) { return mastery >= 80 ? 'strong' : mastery >= 60 ? 'medium' : 'weak' }

function goNext() {
  if (!isGroupComplete(currentGroup.value)) {
    ElMessage.warning('请先完成当前知识点的全部题目')
    return
  }
  activeGroupIndex.value += 1
}

function submitQuiz() {
  if (answeredCount.value !== totalQuestions.value) {
    ElMessage.warning('请完成全部题目后再提交')
    return
  }

  const knowledgeDetails = groups.value.map(group => {
    const correct = group.questions.filter(question => answers[question.id] === question.answer).length
    return { id: group.id, name: group.name, subject: group.subject, correct, total: group.questions.length, mastery: Math.round(correct / group.questions.length * 100) }
  })
  const subjectScores = Object.fromEntries(subjects.value.map(subject => {
    const subjectGroups = groups.value.filter(group => group.subject === subject)
    const questions = subjectGroups.flatMap(group => group.questions)
    const correct = questions.filter(question => answers[question.id] === question.answer).length
    return [subject, Math.round(correct / questions.length * 150)]
  }))
  const correctCount = allQuestions.value.filter(question => answers[question.id] === question.answer).length
  const durationSeconds = Math.max(elapsedSeconds.value, totalQuestions.value * 8)
  const secondsPerQuestion = durationSeconds / totalQuestions.value
  const speed = Math.round(Math.max(20, Math.min(100, 100 - Math.max(0, secondsPerQuestion - 35) * 1.4)))
  const weakest = [...knowledgeDetails].sort((a, b) => a.mastery - b.mastery)[0]

  store.completeDiagnostic({
    answers: { ...answers },
    subjectScores,
    knowledge: Math.round(correctCount / totalQuestions.value * 100),
    speed,
    mistakeType: weakest ? weakest.name : '暂无明显薄弱项',
    weeklyHours: store.weeklyHours,
    knowledgeDetails,
    correctCount,
    totalQuestions: totalQuestions.value,
    durationSeconds
  })
  window.clearInterval(timer)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function restart() {
  store.resetDiagnostic()
  Object.keys(answers).forEach(key => delete answers[key])
  activeGroupIndex.value = 0
  window.location.reload()
}
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}.page-intro{display:flex;align-items:flex-start;justify-content:space-between}.page-intro h2{color:var(--ink);font-size:1.7rem}.page-intro p{margin-top:5px;color:var(--text-secondary)}.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}.quiz-progress-card{display:grid;grid-template-columns:150px 1fr;align-items:center;gap:20px;padding:18px 22px;border:1px solid var(--line);border-radius:17px;background:#fff}.quiz-progress-card>div{display:flex;justify-content:space-between}.quiz-progress-card span,.quiz-progress-card small{color:var(--text-muted);font-size:.72rem}.quiz-progress-card strong{color:var(--ink)}.quiz-progress-card small{grid-column:1/-1;margin-top:-12px}.quiz-layout{display:grid;grid-template-columns:270px minmax(0,1fr);gap:18px;align-items:start}.knowledge-nav{position:sticky;top:98px;padding:18px;border:1px solid var(--line);border-radius:18px;background:#fff}.nav-title h3{color:var(--ink);font-size:.94rem}.subject-group{margin-top:18px}.subject-group>strong{display:block;margin-bottom:7px;color:var(--text-muted);font-size:.72rem}.subject-group button{width:100%;display:flex;align-items:center;gap:9px;padding:10px;border:0;border-radius:11px;text-align:left;background:transparent;cursor:pointer}.subject-group button:hover{background:#f5f8fd}.subject-group button.active{background:#eaf2ff}.subject-group button>span:first-child{width:26px;height:26px;display:grid;place-items:center;flex:0 0 auto;border-radius:8px;color:var(--text-muted);font-size:.7rem;font-weight:800;background:#edf1f6}.subject-group button.active>span:first-child{color:#fff;background:var(--primary)}.subject-group button.complete:not(.active)>span:first-child{color:#fff;background:var(--mint)}.subject-group button b,.subject-group button small{display:block}.subject-group button b{color:var(--ink);font-size:.76rem}.subject-group button small{color:var(--text-muted);font-size:.65rem}.question-panel{min-width:0}.knowledge-heading{display:flex;align-items:flex-start;justify-content:space-between;padding:22px;border:1px solid #dce6f4;border-radius:18px 18px 0 0;background:linear-gradient(135deg,#f8fbff,#edf4ff)}.knowledge-heading span,.knowledge-heading p{color:var(--text-muted);font-size:.72rem}.knowledge-heading h3{margin:3px 0;color:var(--ink);font-size:1.25rem}.question-card{display:flex;gap:16px;padding:24px;border:1px solid var(--line);border-top:0;background:#fff}.question-number{width:34px;height:34px;display:grid;place-items:center;flex:0 0 auto;border-radius:10px;color:var(--primary);font-size:.72rem;font-weight:900;background:var(--primary-soft)}.question-content{flex:1}.question-content h4{margin:5px 0 16px;color:var(--ink);font-size:.94rem}.option-list{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;width:100%}:deep(.option-list .el-radio){width:100%;height:auto;min-height:44px;margin:0;padding:11px 13px;border-radius:11px}:deep(.option-list .el-radio__label){white-space:normal}.option-letter{display:inline-grid;place-items:center;width:22px;height:22px;margin-right:7px;border-radius:6px;color:var(--text-secondary);font-size:.68rem;background:#eef2f7}.quiz-actions{display:flex;align-items:center;gap:12px;padding:18px 22px;border:1px solid var(--line);border-top:0;border-radius:0 0 18px 18px;background:#fff}.quiz-actions>span{flex:1;text-align:center;color:var(--text-muted);font-size:.72rem}.quiz-actions .group-done{display:flex;justify-content:center;align-items:center;gap:5px;color:var(--mint)}.result-hero{display:grid;grid-template-columns:190px 1fr;gap:24px;align-items:center;padding:28px;border-radius:22px;color:#dce8f9;background:linear-gradient(135deg,#14233e,#234875)}.result-score{padding-right:24px;border-right:1px solid rgba(255,255,255,.15)}.result-score span,.result-score small{color:#9fb5d3;font-size:.72rem}.result-score strong{display:inline-block;margin:0 7px;color:#fff;font-size:3rem}.result-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.result-metrics div{padding:13px;border-radius:12px;background:rgba(255,255,255,.07)}.result-metrics small,.result-metrics strong{display:block}.result-metrics small{color:#9fb5d3;font-size:.65rem}.result-metrics strong{margin-top:4px;color:#fff;font-size:.85rem}.result-grid{display:grid;grid-template-columns:.8fr 1.2fr;gap:18px}.result-card{border-radius:19px;border-color:var(--line)}.card-heading{display:flex;align-items:center;justify-content:space-between}.card-heading h3{color:var(--ink)}.card-heading>span{color:var(--text-muted);font-size:.7rem}.subject-results{display:flex;flex-direction:column;gap:18px}.subject-results>div>div{display:flex;justify-content:space-between;margin-bottom:7px}.subject-results strong{color:var(--ink);font-size:.8rem}.subject-results b{color:var(--primary);font-size:.82rem}.knowledge-results{display:flex;flex-direction:column;gap:9px}.knowledge-results>div{display:flex;align-items:center;gap:11px;padding:11px;border-radius:12px;background:#f6f8fc}.knowledge-results>div>span{width:43px;height:43px;display:grid;place-items:center;border-radius:11px;font-size:.72rem;font-weight:900}.knowledge-results>div>span.strong{color:#08765a;background:#ddf6ed}.knowledge-results>div>span.medium{color:#2867d8;background:#e5efff}.knowledge-results>div>span.weak{color:#b06b00;background:#fff0ce}.knowledge-results>div>div{flex:1}.knowledge-results strong,.knowledge-results small{display:block}.knowledge-results strong{color:var(--ink);font-size:.78rem}.knowledge-results small{color:var(--text-muted);font-size:.67rem}.result-actions{display:flex;justify-content:flex-end;gap:12px}
@media(max-width:1050px){.quiz-layout{grid-template-columns:1fr}.knowledge-nav{position:static}.result-hero{grid-template-columns:1fr}.result-score{border-right:0;border-bottom:1px solid rgba(255,255,255,.15);padding:0 0 18px}.result-grid{grid-template-columns:1fr}}@media(max-width:700px){.option-list,.result-metrics{grid-template-columns:1fr}.quiz-progress-card{grid-template-columns:1fr}.quiz-progress-card small{grid-column:auto;margin:0}.quiz-actions{align-items:stretch;flex-direction:column}.quiz-actions>span{order:-1}.question-card{padding:18px 14px}.result-actions{flex-direction:column}.result-actions .el-button{width:100%;margin:0}}
</style>
