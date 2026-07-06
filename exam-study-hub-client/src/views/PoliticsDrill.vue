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
              :aria-label="progress.isKnown(card.key) ? `取消第 ${card.no} 条掌握标记` : `标记第 ${card.no} 条已掌握`"
              :title="progress.isKnown(card.key) ? '取消掌握标记' : '标记已掌握'"
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

<style scoped lang="less" src="../styles/views/PoliticsDrill.less"></style>
