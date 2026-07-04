<template>
  <div class="math-page page-stack">
    <section class="page-intro">
      <div>
        <span class="section-kicker">数学特训</span>
        <h2>成人专升本高数专项</h2>
        <p>{{ subjectHint }}</p>
      </div>
      <el-tag effect="plain">已掌握 {{ knownTopicCount }} / {{ topicCards.length }}</el-tag>
    </section>

    <section class="math-hero">
      <div class="hero-main">
        <span>{{ activeMeta.role }}</span>
        <strong>{{ activeMeta.short }} · {{ activeMeta.category }}</strong>
        <p>{{ activeMeta.focus }}</p>
      </div>
      <div class="hero-stat">
        <small>知识点</small>
        <b>{{ topicCards.length }}</b>
      </div>
      <div class="hero-stat">
        <small>选择题</small>
        <b>{{ totalQuestions }}</b>
      </div>
      <el-button plain @click="markVisible(true)">
        <el-icon><Check /></el-icon>
        本页全标掌握
      </el-button>
    </section>

    <section class="math-toolbar">
      <div class="toolbar-left">
        <el-select v-model="activeSubject" filterable class="subject-select" size="large" aria-label="数学科目">
          <el-option v-for="subject in subjects" :key="subject" :label="subjectLabel(subject)" :value="subject" />
        </el-select>
        <el-select v-model="activeTopicName" filterable class="topic-select" size="large" aria-label="知识点">
          <el-option label="全部知识点" value="all" />
          <el-option v-for="topic in topicCards" :key="topic.name" :label="topic.name" :value="topic.name" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-checkbox v-model="onlyUnknown" label="只看未掌握" border />
        <el-button @click="resetAnswers">
          <el-icon><Refresh /></el-icon>
          重做本页题
        </el-button>
      </div>
    </section>

    <section class="topic-grid">
      <article
        v-for="topic in visibleTopics"
        :key="topic.name"
        class="math-topic-card"
        :class="{ known: progress.isKnown(topic.key) }"
      >
        <div class="topic-head">
          <span class="topic-no">{{ topic.index + 1 }}</span>
          <div>
            <h3>{{ topic.name }}</h3>
            <p>
              <el-tag size="small" effect="plain">{{ topic.guide.level }}</el-tag>
              <span>本组 {{ topicCorrectCount(topic) }}/{{ topic.questions.length }} 题已答对</span>
            </p>
          </div>
          <el-button
            class="known-toggle"
            :type="progress.isKnown(topic.key) ? 'success' : 'default'"
            :plain="!progress.isKnown(topic.key)"
            round
            :aria-label="progress.isKnown(topic.key) ? `取消 ${topic.name} 掌握标记` : `标记 ${topic.name} 已掌握`"
            :title="progress.isKnown(topic.key) ? '取消掌握标记' : '标记已掌握'"
            @click="progress.toggle(topic.key)"
          >
            <el-icon><Check /></el-icon>
            {{ progress.isKnown(topic.key) ? '已掌握' : '标记掌握' }}
          </el-button>
        </div>

        <div class="guide-grid">
          <div class="guide-block">
            <h4><el-icon><Tickets /></el-icon>公式</h4>
            <ul>
              <li v-for="formula in topic.guide.formulas" :key="formula">{{ formula }}</li>
            </ul>
          </div>
          <div class="guide-block">
            <h4><el-icon><Compass /></el-icon>思路</h4>
            <ul>
              <li v-for="idea in topic.guide.ideas" :key="idea">{{ idea }}</li>
            </ul>
          </div>
        </div>

        <div v-if="topic.guide.examples.length" class="example-strip">
          <strong>例题：{{ topic.guide.examples[0].stem }}</strong>
          <ol>
            <li v-for="step in topic.guide.examples[0].steps" :key="step">{{ step }}</li>
          </ol>
        </div>

        <div class="question-list">
          <article v-for="(question, questionIndex) in topic.questions" :key="questionIndex" class="question-item">
            <div class="question-head">
              <span>{{ questionIndex + 1 }}</span>
              <strong>{{ question.question }}</strong>
            </div>
            <div class="option-grid">
              <button
                v-for="option in question.options"
                :key="option"
                type="button"
                :class="optionClass(topic, question, questionIndex, option)"
                @click="chooseAnswer(topic, questionIndex, option)"
              >
                <b>{{ optionCode(option) }}</b>
                <span>{{ optionText(option) }}</span>
              </button>
            </div>
            <p v-if="answers[questionKey(topic, questionIndex)]" class="answer-note">
              正确答案：{{ question.answer }} · {{ answerText(question) }}
            </p>
          </article>
        </div>
      </article>

      <el-empty v-if="!visibleTopics.length" description="当前筛选下没有待练知识点" :image-size="72" />
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import mathOne from '../../docs/MathOne.json'
import mathTwo from '../../docs/MathTwo.json'
import { mathSubjectMeta, guideForTopic } from '../data/mathDrillGuides'
import { useApplicationStore } from '../stores/application'
import { useEnglishProgressStore } from '../stores/englishProgress'

const store = useApplicationStore()
const progress = useEnglishProgressStore()
const answers = reactive({})
const subjects = ['高等数学（一）', '高等数学（二）']
const banks = {
  '高等数学（一）': mathOne,
  '高等数学（二）': mathTwo
}

const majorMathSubject = computed(() => store.selectedMajor?.subjects?.find(subject => subject.startsWith('高等数学')) || '')
const activeSubject = ref(majorMathSubject.value || '高等数学（二）')
const activeTopicName = ref('all')
const onlyUnknown = ref(false)

const activeBank = computed(() => banks[activeSubject.value] || mathTwo)
const activeMeta = computed(() => mathSubjectMeta[activeSubject.value] || mathSubjectMeta['高等数学（二）'])
const topicCards = computed(() => (activeBank.value.topics || []).map((topic, index) => ({
  ...topic,
  index,
  key: topicKey(topic.name),
  guide: guideForTopic(activeSubject.value, topic.name)
})))
const filteredTopics = computed(() => activeTopicName.value === 'all'
  ? topicCards.value
  : topicCards.value.filter(topic => topic.name === activeTopicName.value))
const visibleTopics = computed(() => onlyUnknown.value
  ? filteredTopics.value.filter(topic => !progress.isKnown(topic.key))
  : filteredTopics.value)
const totalQuestions = computed(() => topicCards.value.reduce((sum, topic) => sum + topic.questions.length, 0))
const knownTopicCount = computed(() => progress.countKnown(topicCards.value.map(topic => topic.key)))
const subjectHint = computed(() => {
  if (majorMathSubject.value) return `当前专业统考含 ${majorMathSubject.value}，已按成人专升本${activeMeta.value.category}方向组织知识点。`
  return `当前专业统考不含高等数学；这里保留高数一/二专项，适合换专业或补基础时使用。`
})

watch(majorMathSubject, subject => {
  if (subject && subjects.includes(subject)) activeSubject.value = subject
})
watch(activeSubject, () => {
  if (activeTopicName.value !== 'all' && !topicCards.value.some(topic => topic.name === activeTopicName.value)) {
    activeTopicName.value = 'all'
  }
})

function subjectLabel(subject) {
  const meta = mathSubjectMeta[subject]
  return `${meta.short} · ${meta.category}`
}

function topicKey(topicName) {
  return `math-topic:${activeSubject.value}:${topicName}`
}

function questionKey(topic, questionIndex) {
  return `math-q:${activeSubject.value}:${topic.name}:${questionIndex}`
}

function optionCode(option) {
  return String(option).trim().match(/^([A-D])[.、\s]/)?.[1] || ''
}

function optionText(option) {
  return String(option).replace(/^[A-D][.、\s]+/, '')
}

function chooseAnswer(topic, questionIndex, option) {
  answers[questionKey(topic, questionIndex)] = optionCode(option)
}

function optionClass(topic, question, questionIndex, option) {
  const picked = answers[questionKey(topic, questionIndex)]
  const code = optionCode(option)
  return {
    picked: picked === code,
    correct: picked && code === question.answer,
    wrong: picked === code && code !== question.answer
  }
}

function answerText(question) {
  return optionText(question.options.find(option => optionCode(option) === question.answer) || question.answer)
}

function topicCorrectCount(topic) {
  return topic.questions.filter((question, index) => answers[questionKey(topic, index)] === question.answer).length
}

function markVisible(known) {
  progress.markMany(visibleTopics.value.map(topic => topic.key), known)
}

function resetAnswers() {
  visibleTopics.value.forEach(topic => {
    topic.questions.forEach((_, index) => {
      delete answers[questionKey(topic, index)]
    })
  })
}
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}
.page-intro{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}
.page-intro h2{color:var(--ink);font-size:1.55rem}
.page-intro p{margin-top:5px;color:var(--text-secondary);max-width:760px}
.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}
.math-hero{display:grid;grid-template-columns:1fr 112px 112px auto;gap:14px;align-items:center;padding:18px 20px;border:1px solid var(--line);border-radius:var(--radius-lg);background:#fff;box-shadow:var(--shadow-xs)}
.hero-main span,.hero-main p,.hero-stat small{color:var(--text-muted);font-size:.75rem}
.hero-main strong{display:block;margin:3px 0;color:var(--ink);font-size:1.22rem}
.hero-stat{height:78px;display:flex;flex-direction:column;justify-content:center;align-items:center;border:1px solid var(--line);border-radius:var(--radius-md);background:var(--surface-soft)}
.hero-stat b{color:var(--primary);font-size:1.8rem;line-height:1}
.math-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.toolbar-left,.toolbar-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.subject-select{width:220px}
.topic-select{width:260px}
.topic-grid{display:grid;grid-template-columns:1fr;gap:14px}
.math-topic-card{padding:18px;border:1px solid var(--line);border-radius:var(--radius-lg);background:#fff;box-shadow:var(--shadow-xs);transition:.18s ease}
.math-topic-card:hover{box-shadow:var(--shadow-sm)}
.math-topic-card.known{border-color:#c9efdf;background:#f5fbf8}
.topic-head{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:flex-start;gap:12px;margin-bottom:14px}
.topic-no{width:32px;height:32px;display:grid;place-items:center;flex:0 0 auto;border-radius:9px;color:var(--primary);font-size:.76rem;font-weight:900;background:var(--primary-soft)}
.topic-head h3{color:var(--ink);font-size:1.02rem}
.topic-head>div{min-width:0}
.topic-head p{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:5px;color:var(--text-muted);font-size:.74rem}
.known-toggle{min-height:44px;margin-left:0;padding:0 14px;white-space:nowrap}
.guide-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.guide-block{padding:14px;border:1px solid var(--line);border-radius:var(--radius-md);background:var(--surface-soft)}
.guide-block h4{display:flex;align-items:center;gap:6px;margin-bottom:8px;color:var(--ink);font-size:.86rem}
.guide-block h4 .el-icon{color:var(--primary)}
.guide-block ul{display:flex;flex-direction:column;gap:6px;padding-left:18px;color:var(--text-secondary);font-size:.78rem;line-height:1.55}
.example-strip{margin-top:12px;padding:13px 14px;border-radius:var(--radius-md);border:1px solid #f0dbb4;background:var(--accent-soft)}
.example-strip strong{display:block;color:#8a5600;font-size:.84rem}
.example-strip ol{margin-top:7px;padding-left:18px;color:#7a5a21;font-size:.78rem;line-height:1.65}
.question-list{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:14px}
.question-item{padding:14px;border:1px solid var(--line);border-radius:var(--radius-md);background:#fff}
.question-head{display:flex;align-items:flex-start;gap:8px;margin-bottom:10px}
.question-head span{width:24px;height:24px;display:grid;place-items:center;flex:0 0 auto;border-radius:8px;color:var(--primary);font-size:.7rem;font-weight:900;background:var(--primary-soft)}
.question-head strong{color:var(--ink);font-size:.86rem;line-height:1.5}
.option-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.option-grid button{min-height:44px;display:flex;align-items:flex-start;gap:8px;padding:9px 10px;border:1px solid #dfe7f3;border-radius:var(--radius-sm);color:var(--text-secondary);font:inherit;font-size:.78rem;text-align:left;background:#fff;cursor:pointer;transition:.16s ease}
.option-grid button:hover{border-color:#bcd3f7;color:var(--primary)}
.option-grid button b{color:var(--ink)}
.option-grid button.correct{border-color:#bfe8cf;color:#147a55;background:#f1fbf5}
.option-grid button.wrong{border-color:#ffc7c7;color:#b42323;background:#fff1f1}
.option-grid button.picked:not(.correct):not(.wrong){border-color:var(--primary);background:#f3f7ff}
.answer-note{margin-top:9px;color:var(--text-muted);font-size:.74rem}
@media(max-width:980px){.math-hero{grid-template-columns:1fr 1fr}.question-list{grid-template-columns:1fr}}
@media(max-width:700px){.page-intro,.math-toolbar{align-items:stretch;flex-direction:column}.math-hero,.guide-grid,.option-grid{grid-template-columns:1fr}.topic-head{grid-template-columns:auto minmax(0,1fr)}.known-toggle{grid-column:2;justify-self:start}.subject-select,.topic-select{width:100%}}
</style>
