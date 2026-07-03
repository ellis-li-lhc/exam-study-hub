<template>
  <div class="politics-page page-stack">
    <section class="page-intro">
      <div>
        <span class="section-kicker">政治特训</span>
        <h2>按成人专升本政治板块训练</h2>
        <p>{{ activeSection.desc }}</p>
      </div>
      <el-tag effect="plain">已掌握 {{ totalKnown }} / {{ totalCount }}</el-tag>
    </section>

    <section class="section-switch" aria-label="政治考试板块">
      <button
        v-for="section in sections"
        :key="section.id"
        type="button"
        :class="{ active: activeSectionId === section.id }"
        @click="setSection(section.id)"
      >
        <span>{{ section.short }}</span>
        <strong>{{ section.title }}</strong>
        <small>{{ sectionStats(section).memory }} 记忆 · {{ sectionStats(section).questions }} 题</small>
      </button>
    </section>

    <section class="focus-strip">
      <span v-for="item in activeSection.focus" :key="item">{{ item }}</span>
    </section>

    <el-tabs v-model="activeTab" class="drill-tabs">
      <el-tab-pane name="memory">
        <template #label><span class="tab-label">知识速记 · {{ sectionMemory.length }}</span></template>

        <div class="toolbar">
          <el-select v-model="currentBatch" filterable size="default" class="batch-select" aria-label="知识速记分组">
            <el-option v-for="opt in batchOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <div class="toolbar-right">
            <el-checkbox v-model="onlyUnknown" label="只看未掌握" border />
            <el-button size="small" @click="showAll = !showAll">{{ showAll ? '隐藏全部答案' : '显示全部答案' }}</el-button>
            <el-button size="small" plain @click="markBatch(true)">本组全标掌握</el-button>
          </div>
        </div>

        <div class="mem-grid">
          <article v-for="card in visibleCards" :key="card.key" class="mem-card" :class="{ known: progress.isKnown(card.key) }">
            <div class="mem-no">{{ card.no }}</div>
            <div class="mem-body">
              <p class="mem-q">{{ card.q }}</p>
              <p v-if="showAll || revealed.has(card.key)" class="mem-a">{{ card.a }}</p>
              <el-button v-else size="small" text type="primary" @click="reveal(card.key)">显示答案</el-button>
            </div>
            <el-button
              class="mark-btn"
              :type="progress.isKnown(card.key) ? 'success' : 'default'"
              :plain="!progress.isKnown(card.key)"
              circle
              @click="progress.toggle(card.key)"
            >
              <el-icon><Check /></el-icon>
            </el-button>
          </article>
          <el-empty v-if="!visibleCards.length" description="当前筛选下没有待背知识点" :image-size="64" />
        </div>

        <div class="pager">
          <el-button :disabled="currentBatch === 0" @click="currentBatch--">上一组</el-button>
          <span>第 {{ currentBatch + 1 }} / {{ batchCount }} 组</span>
          <el-button :disabled="currentBatch >= batchCount - 1" @click="currentBatch++">下一组</el-button>
        </div>
      </el-tab-pane>

      <el-tab-pane name="quiz">
        <template #label><span class="tab-label">选择题 · {{ sectionQuestions.length }}</span></template>

        <div class="toolbar quiz-toolbar">
          <el-select v-model="quizTopicName" filterable size="default" class="topic-select" aria-label="选择题主题">
            <el-option label="全部主题" value="all" />
            <el-option v-for="topic in quizTopics" :key="topic.name" :label="`${topic.name} · ${topic.questions.length}题`" :value="topic.name" />
          </el-select>
          <el-button size="small" @click="resetQuizAnswers">
            <el-icon><Refresh /></el-icon>
            重做当前题
          </el-button>
        </div>

        <div class="quiz-grid">
          <article v-for="item in visibleQuestions" :key="item.key" class="quiz-card">
            <div class="quiz-head">
              <span>{{ item.order }}</span>
              <div>
                <el-tag size="small" effect="plain">{{ item.topicName }}</el-tag>
                <strong>{{ item.question.question }}</strong>
              </div>
            </div>
            <div class="option-grid">
              <button
                v-for="option in item.question.options"
                :key="option"
                type="button"
                :class="optionClass(item, option)"
                @click="chooseAnswer(item, option)"
              >
                <b>{{ optionCode(option) }}</b>
                <span>{{ optionText(option) }}</span>
              </button>
            </div>
            <p v-if="quizAnswers[item.key]" class="answer-note">正确答案：{{ item.question.answer }} · {{ answerText(item.question) }}</p>
          </article>
          <el-empty v-if="!visibleQuestions.length" description="当前板块暂无选择题" :image-size="72" />
        </div>
      </el-tab-pane>

      <el-tab-pane name="essay">
        <template #label><span class="tab-label">简答背诵 · {{ sectionEssays.length }}</span></template>

        <div class="toolbar">
          <el-select v-model="essayBatch" filterable size="default" class="batch-select" aria-label="简答题分组">
            <el-option v-for="opt in essayBatchOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <el-checkbox v-model="onlyEssayUnknown" label="只看未掌握" border />
        </div>

        <el-collapse class="essay-list">
          <el-collapse-item v-for="item in visibleEssays" :key="item.key" :name="item.key">
            <template #title>
              <span class="essay-title" :class="{ known: progress.isKnown(item.key) }">
                <span class="essay-no">{{ item.no }}</span>
                <span class="essay-q">{{ item.q }}</span>
                <el-icon v-if="progress.isKnown(item.key)" class="essay-done"><CircleCheck /></el-icon>
              </span>
            </template>
            <div class="essay-answer">{{ item.a }}</div>
            <div class="essay-foot">
              <el-button
                size="small"
                :type="progress.isKnown(item.key) ? 'success' : 'primary'"
                :plain="!progress.isKnown(item.key)"
                round
                @click="progress.toggle(item.key)"
              >
                <el-icon><Check /></el-icon>
                {{ progress.isKnown(item.key) ? '已掌握' : '标记掌握' }}
              </el-button>
            </div>
          </el-collapse-item>
        </el-collapse>
        <el-empty v-if="!visibleEssays.length" description="当前筛选下没有待背简答题" :image-size="72" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { politicsSections, sectionById } from '../data/politicsSections'
import { useEnglishProgressStore } from '../stores/englishProgress'
import knowledgeBank from '../../docs/PoliticsKnowledge.json'
import questionBank from '../../docs/Politics.json'

const progress = useEnglishProgressStore()
const sections = politicsSections
const activeSectionId = ref(sections[0].id)
const activeTab = ref('memory')
const BATCH_SIZE = 18
const currentBatch = ref(0)
const essayBatch = ref(0)
const onlyUnknown = ref(false)
const onlyEssayUnknown = ref(false)
const showAll = ref(false)
const revealed = ref(new Set())
const quizTopicName = ref('all')
const quizAnswers = reactive({})

const activeSection = computed(() => sectionById(activeSectionId.value))
const memorySource = computed(() => [
  ...knowledgeBank.memory,
  ...(activeSection.value.supplementalMemory || []).map(item => ({ ...item, category: activeSection.value.title, supplemental: true }))
])
const essaySource = computed(() => [
  ...knowledgeBank.essay,
  ...(activeSection.value.supplementalEssay || []).map(item => ({ ...item, category: activeSection.value.title, supplemental: true }))
])

const sectionMemory = computed(() => memorySource.value
  .map((item, index) => ({ ...item, sourceIndex: index }))
  .filter(item => activeSection.value.memoryCategories.includes(item.category) || item.supplemental)
  .map((item, index) => ({ ...item, no: index + 1, key: memoryKey(activeSection.value.id, item.sourceIndex, index) })))
const sectionEssays = computed(() => essaySource.value
  .map((item, index) => ({ ...item, sourceIndex: index }))
  .filter(item => activeSection.value.memoryCategories.includes(item.category) || item.supplemental)
  .map((item, index) => ({ ...item, no: index + 1, key: essayKey(activeSection.value.id, item.sourceIndex, index) })))
const quizTopics = computed(() => {
  const base = (questionBank.topics || [])
    .filter(topic => activeSection.value.topicNames.includes(topic.name))
    .map(topic => ({ ...topic, supplemental: false }))
  if (activeSection.value.supplementalQuestions?.length) {
    base.push({
      name: '时事综合补充',
      supplemental: true,
      questions: activeSection.value.supplementalQuestions
    })
  }
  return base
})
const sectionQuestions = computed(() => quizTopics.value.flatMap(topic => topic.questions))
const activeQuizTopics = computed(() => quizTopicName.value === 'all'
  ? quizTopics.value
  : quizTopics.value.filter(topic => topic.name === quizTopicName.value))
const visibleQuestions = computed(() => activeQuizTopics.value.flatMap(topic => topic.questions.map((question, index) => ({
  topicName: topic.name,
  question,
  index,
  key: quizKey(activeSection.value.id, topic.name, index)
}))).map((item, index) => ({ ...item, order: index + 1 })))

const batchCount = computed(() => Math.max(1, Math.ceil(sectionMemory.value.length / BATCH_SIZE)))
const batchOptions = computed(() => buildBatchOptions(sectionMemory.value.length, batchCount.value))
const currentCards = computed(() => sectionMemory.value.slice(currentBatch.value * BATCH_SIZE, currentBatch.value * BATCH_SIZE + BATCH_SIZE))
const visibleCards = computed(() => onlyUnknown.value ? currentCards.value.filter(card => !progress.isKnown(card.key)) : currentCards.value)

const essayBatchCount = computed(() => Math.max(1, Math.ceil(sectionEssays.value.length / BATCH_SIZE)))
const essayBatchOptions = computed(() => buildBatchOptions(sectionEssays.value.length, essayBatchCount.value))
const currentEssays = computed(() => sectionEssays.value.slice(essayBatch.value * BATCH_SIZE, essayBatch.value * BATCH_SIZE + BATCH_SIZE))
const visibleEssays = computed(() => onlyEssayUnknown.value ? currentEssays.value.filter(item => !progress.isKnown(item.key)) : currentEssays.value)

const allMemoryKeys = computed(() => sections.flatMap(section => sectionCardsFor(section).map(item => item.key)))
const allEssayKeys = computed(() => sections.flatMap(section => sectionEssaysFor(section).map(item => item.key)))
const totalCount = computed(() => allMemoryKeys.value.length + allEssayKeys.value.length)
const totalKnown = computed(() => progress.countKnown(allMemoryKeys.value) + progress.countKnown(allEssayKeys.value))

watch(activeSectionId, () => {
  currentBatch.value = 0
  essayBatch.value = 0
  quizTopicName.value = 'all'
  showAll.value = false
  revealed.value = new Set()
})
watch(sectionMemory, () => {
  if (currentBatch.value > batchCount.value - 1) currentBatch.value = 0
})
watch(sectionEssays, () => {
  if (essayBatch.value > essayBatchCount.value - 1) essayBatch.value = 0
})

function setSection(id) {
  activeSectionId.value = id
}

function buildBatchOptions(total, count) {
  return Array.from({ length: count }, (_, index) => {
    const start = total ? index * BATCH_SIZE + 1 : 0
    const end = Math.min((index + 1) * BATCH_SIZE, total)
    return { value: index, label: total ? `第 ${index + 1} 组 · ${start}-${end}` : '暂无分组' }
  })
}

function memoryKey(sectionId, sourceIndex, localIndex) {
  return `pol-memory:${sectionId}:${sourceIndex}:${localIndex}`
}

function essayKey(sectionId, sourceIndex, localIndex) {
  return `pol-essay:${sectionId}:${sourceIndex}:${localIndex}`
}

function quizKey(sectionId, topicName, index) {
  return `pol-quiz:${sectionId}:${topicName}:${index}`
}

function sectionCardsFor(section) {
  const extra = (section.supplementalMemory || []).map(item => ({ ...item, category: section.title, supplemental: true }))
  return [...knowledgeBank.memory, ...extra]
    .map((item, sourceIndex) => ({ ...item, sourceIndex }))
    .filter(item => section.memoryCategories.includes(item.category) || item.supplemental)
    .map((item, index) => ({ ...item, key: memoryKey(section.id, item.sourceIndex, index) }))
}

function sectionEssaysFor(section) {
  const extra = (section.supplementalEssay || []).map(item => ({ ...item, category: section.title, supplemental: true }))
  return [...knowledgeBank.essay, ...extra]
    .map((item, sourceIndex) => ({ ...item, sourceIndex }))
    .filter(item => section.memoryCategories.includes(item.category) || item.supplemental)
    .map((item, index) => ({ ...item, key: essayKey(section.id, item.sourceIndex, index) }))
}

function sectionStats(section) {
  const questions = (questionBank.topics || [])
    .filter(topic => section.topicNames.includes(topic.name))
    .reduce((sum, topic) => sum + topic.questions.length, 0) + (section.supplementalQuestions?.length || 0)
  return {
    memory: sectionCardsFor(section).length,
    questions
  }
}

function reveal(key) {
  const next = new Set(revealed.value)
  next.add(key)
  revealed.value = next
}

function markBatch(known) {
  progress.markMany(currentCards.value.map(card => card.key), known)
}

function optionCode(option) {
  return String(option).trim().match(/^([A-D])[.、\s]/)?.[1] || ''
}

function optionText(option) {
  return String(option).replace(/^[A-D][.、\s]+/, '')
}

function chooseAnswer(item, option) {
  quizAnswers[item.key] = optionCode(option)
}

function optionClass(item, option) {
  const picked = quizAnswers[item.key]
  const code = optionCode(option)
  return {
    picked: picked === code,
    correct: picked && code === item.question.answer,
    wrong: picked === code && code !== item.question.answer
  }
}

function answerText(question) {
  return optionText(question.options.find(option => optionCode(option) === question.answer) || question.answer)
}

function resetQuizAnswers() {
  visibleQuestions.value.forEach(item => {
    delete quizAnswers[item.key]
  })
}
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:16px}
.page-intro{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}
.page-intro h2{color:var(--ink);font-size:1.55rem}
.page-intro p{margin-top:5px;color:var(--text-secondary);font-size:.82rem;max-width:720px}
.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}
.section-switch{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.section-switch button{min-height:94px;padding:14px 16px;border:1px solid var(--line);border-radius:var(--radius-md);text-align:left;background:#fff;cursor:pointer;transition:.18s ease}
.section-switch button:hover{border-color:#bfd4ff;box-shadow:var(--shadow-sm)}
.section-switch button.active{border-color:#c6d7f6;background:var(--primary-faint)}
.section-switch span{display:inline-grid;place-items:center;min-width:38px;height:24px;margin-bottom:8px;border-radius:999px;color:var(--primary);font-size:.7rem;font-weight:900;background:var(--primary-soft)}
.section-switch strong{display:block;color:var(--ink);font-size:.9rem;line-height:1.35}
.section-switch small{display:block;margin-top:5px;color:var(--text-muted);font-size:.72rem}
.focus-strip{display:flex;flex-wrap:wrap;gap:8px}
.focus-strip span{padding:6px 11px;border:1px solid var(--line);border-radius:999px;color:var(--text-secondary);font-size:.74rem;background:#fff}
.tab-label{font-size:.9rem;font-weight:700}
.toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px;flex-wrap:wrap}
.toolbar-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.batch-select{width:220px}
.topic-select{width:260px}
.quiz-toolbar{justify-content:flex-start}
.mem-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.mem-card{display:flex;gap:10px;padding:15px 16px;border:1px solid var(--line);border-radius:var(--radius-md);background:#fff;box-shadow:var(--shadow-xs);transition:box-shadow .18s,border-color .18s}
.mem-card:hover{box-shadow:0 6px 16px rgba(37,99,235,.07)}
.mem-card.known{border-color:#bfe8cf;background:#f6fffb}
.mem-no{width:26px;height:26px;display:grid;place-items:center;flex:0 0 auto;border-radius:8px;color:var(--primary);font-size:.66rem;font-weight:800;background:var(--primary-soft)}
.mem-card.known .mem-no{color:#fff;background:var(--mint)}
.mem-body{flex:1;min-width:0}
.mem-q{color:var(--ink);font-size:.86rem;line-height:1.55}
.mem-a{margin-top:10px;padding:10px 12px;border-radius:10px;background:#eef7f2;color:#15795a;font-size:.84rem;line-height:1.6;font-weight:600}
.mark-btn{flex:0 0 auto;align-self:flex-start}
.pager{display:flex;align-items:center;justify-content:center;gap:16px;margin-top:16px;color:var(--text-secondary);font-size:.8rem}
.quiz-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.quiz-card{padding:15px;border:1px solid var(--line);border-radius:var(--radius-md);background:#fff;box-shadow:var(--shadow-xs)}
.quiz-head{display:flex;align-items:flex-start;gap:9px;margin-bottom:12px}
.quiz-head>span{width:26px;height:26px;display:grid;place-items:center;flex:0 0 auto;border-radius:8px;color:var(--primary);font-size:.7rem;font-weight:900;background:var(--primary-soft)}
.quiz-head strong{display:block;margin-top:7px;color:var(--ink);font-size:.88rem;line-height:1.55}
.option-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.option-grid button{min-height:44px;display:flex;align-items:flex-start;gap:8px;padding:9px 10px;border:1px solid #dfe7f3;border-radius:var(--radius-sm);color:var(--text-secondary);font:inherit;font-size:.78rem;text-align:left;background:#fff;cursor:pointer;transition:.16s ease}
.option-grid button:hover{border-color:#bcd3f7;color:var(--primary)}
.option-grid button b{color:var(--ink)}
.option-grid button.correct{border-color:#bfe8cf;color:#147a55;background:#f1fbf5}
.option-grid button.wrong{border-color:#ffc7c7;color:#b42323;background:#fff1f1}
.option-grid button.picked:not(.correct):not(.wrong){border-color:var(--primary);background:#f3f7ff}
.answer-note{margin-top:9px;color:var(--text-muted);font-size:.74rem}
.essay-list{border:0}
:deep(.essay-list){--el-collapse-border-color:transparent}
:deep(.essay-list .el-collapse-item){margin-bottom:10px;border:1px solid var(--line);border-radius:var(--radius-md);overflow:hidden;background:#fff;box-shadow:var(--shadow-xs);transition:box-shadow .18s}
:deep(.essay-list .el-collapse-item.is-active){box-shadow:0 6px 18px rgba(37,99,235,.08);border-color:#bcd3f7}
:deep(.essay-list .el-collapse-item__header){height:auto;min-height:56px;padding:14px 16px;border-bottom:0;line-height:1.5}
:deep(.essay-list .el-collapse-item__wrap){border-bottom:0}
:deep(.essay-list .el-collapse-item__content){padding:0 16px 16px}
.essay-title{display:flex;align-items:center;gap:10px;width:100%;color:var(--ink);font-size:.9rem;font-weight:600}
.essay-no{width:26px;height:26px;display:grid;place-items:center;flex:0 0 auto;border-radius:8px;color:var(--primary);font-size:.7rem;font-weight:800;background:var(--primary-soft)}
.essay-q{flex:1;min-width:0}
.essay-title.known .essay-no{color:#fff;background:var(--mint)}
.essay-done{color:#15a05a;flex:0 0 auto}
.essay-answer{white-space:pre-wrap;padding:14px 16px;border-radius:var(--radius-md);background:var(--surface-soft);color:var(--text-secondary);font-size:.82rem;line-height:1.8}
.essay-foot{display:flex;justify-content:flex-end;margin-top:12px}
@media(max-width:960px){.section-switch,.mem-grid,.quiz-grid{grid-template-columns:1fr}}
@media(max-width:640px){.page-intro,.toolbar{align-items:stretch;flex-direction:column}.toolbar-right{align-items:stretch}.batch-select,.topic-select{width:100%}.option-grid{grid-template-columns:1fr}}
</style>
