<template>
  <div class="drill-page page-stack">
    <section class="page-intro">
      <div><span class="section-kicker">英语特训</span><h2>先把单词地基打牢</h2><p>核心词、造句框架、固定搭配、基础语法，每块都能边学边测、记录掌握进度。基础越弱，越要先过单词关。</p></div>
    </section>

    <el-tabs v-model="activeTab" class="drill-tabs">
      <!-- Tab 1: 3500 核心词 -->
      <el-tab-pane name="words">
        <template #label><span class="tab-label">3500 核心词</span></template>

        <section class="drill-hero">
          <div class="hero-score"><span>已掌握单词</span><strong>{{ store.knownCount }}</strong><small>/ {{ store.totalCount }} 词</small></div>
          <div class="hero-progress">
            <el-progress :percentage="store.masteryPercent" :stroke-width="14" :text-inside="true" />
            <p>共 {{ store.batchCount }} 组，每组 {{ store.batchSize }} 词。当前第 {{ store.currentBatch + 1 }} 组已掌握 {{ store.currentBatchKnown }}/{{ store.currentWords.length }}。</p>
          </div>
          <el-button class="hero-reset" plain @click="confirmReset"><el-icon><Refresh /></el-icon>重置进度</el-button>
        </section>

        <section class="drill-toolbar">
          <div class="toolbar-left">
            <el-button :disabled="store.currentBatch === 0" @click="store.setBatch(store.currentBatch - 1)"><el-icon><ArrowLeft /></el-icon>上一组</el-button>
            <el-select :model-value="store.currentBatch" class="batch-select" @change="store.setBatch($event)">
              <el-option v-for="option in store.batchOptions" :key="option.value" :label="option.label" :value="option.value" />
            </el-select>
            <el-button :disabled="store.currentBatch === store.batchCount - 1" @click="store.setBatch(store.currentBatch + 1)">下一组<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button>
          </div>
          <div class="toolbar-right">
            <el-checkbox v-model="onlyUnknown" label="只看未掌握" border />
            <el-button @click="store.markCurrentBatch(true)">本组全标已掌握</el-button>
            <el-button type="primary" @click="startVocabTest"><el-icon><EditPen /></el-icon>本组自测</el-button>
          </div>
        </section>

        <section class="word-grid">
          <article v-for="word in visibleWords" :key="word.id" class="word-card" :class="{ known: store.isKnown(word.id) }">
            <div class="word-main">
              <div class="word-top">
                <strong class="speakable" @click="speak(word.word)">{{ word.word }}</strong>
                <el-button class="speak-btn" text circle @click="speak(word.word)"><el-icon><VideoPlay /></el-icon></el-button>
                <el-tag v-if="word.tag" size="small" effect="plain">{{ word.tag }}</el-tag>
                <span v-if="word.phonetic" class="phonetic">/{{ word.phonetic }}/</span>
              </div>
              <p class="meaning">{{ word.meaning }}</p>
            </div>
            <el-button class="known-toggle" :type="store.isKnown(word.id) ? 'success' : 'default'" :plain="!store.isKnown(word.id)" circle @click="store.toggleKnown(word.id)"><el-icon><Check /></el-icon></el-button>
          </article>
          <el-empty v-if="visibleWords.length === 0" description="本组单词都已掌握，进入下一组吧" :image-size="80" />
        </section>
      </el-tab-pane>

      <!-- Tab 2: 造句基础 / Tab 3: 核心短语 共用结构 -->
      <el-tab-pane v-for="dataset in itemDatasets" :key="dataset.ns" :name="dataset.ns">
        <template #label><span class="tab-label">{{ dataset.tabLabel }}</span></template>

        <section class="extra-bar">
          <el-alert class="extra-intro" :title="dataset.data.intro" type="info" show-icon :closable="false" />
          <div class="extra-progress"><small>已掌握</small><strong>{{ countKnownItems(dataset) }}/{{ totalItems(dataset) }}</strong></div>
        </section>

        <div class="essential-nav">
          <button v-for="group in dataset.data.groups" :key="group.id" :class="{ active: dataset.activeId.value === group.id }" @click="dataset.activeId.value = group.id">{{ group.short }}</button>
        </div>

        <section class="essential-group">
          <div class="group-head">
            <h3>{{ activeItemGroup(dataset).name }}</h3><span>{{ activeItemGroup(dataset).desc }}</span>
            <div class="group-actions">
              <span class="group-count">本组 {{ groupKnownCount(dataset) }}/{{ activeItemGroup(dataset).words.length }}</span>
              <el-button size="small" type="primary" plain @click="startItemTest(dataset)"><el-icon><EditPen /></el-icon>本组自测</el-button>
            </div>
          </div>
          <div class="essential-grid">
            <article v-for="item in activeItemGroup(dataset).words" :key="item.word" class="essential-card" :class="{ known: progress.isKnown(itemKey(dataset, item)) }">
              <div class="essential-top">
                <strong class="speakable" @click="speak(item.word)">{{ item.word }}</strong>
                <el-button class="speak-btn" text circle @click="speak(item.word)"><el-icon><VideoPlay /></el-icon></el-button>
                <el-tag v-if="item.tag" size="small" effect="plain">{{ item.tag }}</el-tag>
                <el-button class="known-toggle mini" :type="progress.isKnown(itemKey(dataset, item)) ? 'success' : 'default'" :plain="!progress.isKnown(itemKey(dataset, item))" circle @click="progress.toggle(itemKey(dataset, item))"><el-icon><Check /></el-icon></el-button>
              </div>
              <p class="meaning">{{ item.meaning }}</p>
              <p class="example speakable" @click="speak(item.example)"><el-icon><VideoPlay /></el-icon>{{ item.example }}</p>
            </article>
          </div>
        </section>
      </el-tab-pane>

      <!-- Tab 4: 基础语法 -->
      <el-tab-pane name="grammar">
        <template #label><span class="tab-label">基础语法</span></template>

        <section class="extra-bar">
          <el-alert class="extra-intro" :title="grammar.intro" type="info" show-icon :closable="false" />
          <div class="extra-progress"><small>已掌握知识点</small><strong>{{ grammarKnownTotal }}/{{ grammarPointTotal }}</strong></div>
        </section>

        <div class="essential-nav">
          <button v-for="section in grammar.sections" :key="section.id" :class="{ active: activeGrammarId === section.id }" @click="activeGrammarId = section.id">{{ section.short }}</button>
        </div>

        <section class="essential-group">
          <div class="group-head">
            <h3>{{ activeGrammarSection.name }}</h3>
            <div class="group-actions">
              <span class="group-count">本节 {{ grammarSectionKnown }}/{{ activeGrammarSection.points.length }}</span>
              <el-button v-if="activeGrammarSection.quiz && activeGrammarSection.quiz.length" size="small" type="primary" plain @click="startGrammarTest"><el-icon><EditPen /></el-icon>本节自测</el-button>
            </div>
          </div>
          <div class="grammar-list">
            <article v-for="(point, index) in activeGrammarSection.points" :key="index" class="grammar-card" :class="{ known: progress.isKnown(grammarKey(index)) }">
              <div class="grammar-head">
                <h4>{{ point.title }}</h4>
                <el-button class="known-toggle mini" :type="progress.isKnown(grammarKey(index)) ? 'success' : 'default'" :plain="!progress.isKnown(grammarKey(index))" circle @click="progress.toggle(grammarKey(index))"><el-icon><Check /></el-icon></el-button>
              </div>
              <p class="grammar-explain">{{ point.explain }}</p>
              <ul class="grammar-examples">
                <li v-for="(example, exampleIndex) in point.examples" :key="exampleIndex">
                  <span class="ex-en speakable" @click="speak(example.en)"><el-icon><VideoPlay /></el-icon>{{ example.en }}</span>
                  <span class="ex-cn">{{ example.cn }}</span>
                </li>
              </ul>
            </article>
          </div>
        </section>
      </el-tab-pane>
    </el-tabs>

    <!-- 统一自测弹窗 -->
    <el-dialog v-model="testOpen" :title="testTitle" width="min(680px, 94vw)" top="5vh" destroy-on-close class="vocab-test-dialog">
      <template v-if="!testResult">
        <p class="test-tip">共 {{ testQuestions.length }} 题，选择正确选项。</p>
        <article v-for="(question, index) in testQuestions" :key="question.id" class="test-question">
          <div class="test-q-head">
            <span class="q-order">{{ index + 1 }}</span>
            <strong :class="{ speakable: question.speak }" @click="question.speak && speak(question.prompt)">{{ question.prompt }}</strong>
            <el-button v-if="question.speak" class="speak-btn" text circle @click="speak(question.prompt)"><el-icon><VideoPlay /></el-icon></el-button>
            <span v-if="question.hint" class="phonetic">/{{ question.hint }}/</span>
          </div>
          <el-radio-group v-model="testAnswers[question.id]" class="test-options">
            <el-radio v-for="(option, optionIndex) in question.options" :key="optionIndex" :value="option" border>{{ option }}</el-radio>
          </el-radio-group>
        </article>
      </template>
      <div v-else class="test-result">
        <span class="result-mark" :class="testResult.correct === testResult.total ? 'full' : 'partial'"><el-icon><component :is="testResult.correct === testResult.total ? 'CircleCheck' : 'Warning'" /></el-icon></span>
        <h3>答对 {{ testResult.correct }} / {{ testResult.total }}</h3>
        <p v-if="testMarksMastery">{{ testResult.correct === testResult.total ? '全部正确，已标记为掌握。' : '答对的已标记为掌握，答错的已取消标记，建议再过一遍。' }}</p>
        <p v-else>{{ testResult.correct === testResult.total ? '全部正确，掌握得不错。' : '还有错题，建议回顾对应的语法点。' }}</p>
      </div>
      <template #footer>
        <template v-if="!testResult"><el-button @click="testOpen = false">取消</el-button><el-button type="primary" :disabled="answeredCount < testQuestions.length" @click="submitTest">提交（{{ answeredCount }}/{{ testQuestions.length }}）</el-button></template>
        <el-button v-else type="primary" @click="testOpen = false">完成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useVocabularyStore } from '../stores/vocabulary'
import { useEnglishProgressStore } from '../stores/englishProgress'
import essentials from '../../docs/EnglishEssentials.json'
import phrases from '../../docs/EnglishPhrases.json'
import grammar from '../../docs/EnglishGrammar.json'

const store = useVocabularyStore()
const progress = useEnglishProgressStore()
const activeTab = ref('words')
const onlyUnknown = ref(false)

// 造句基础 / 核心短语 共用同一套渲染与逻辑
const itemDatasets = [
  { ns: 'essentials', tabLabel: '造句基础', data: essentials, activeId: ref(essentials.groups[0].id) },
  { ns: 'phrases', tabLabel: '核心短语', data: phrases, activeId: ref(phrases.groups[0].id) }
]
const activeGrammarId = ref(grammar.sections[0].id)
const activeGrammarSection = computed(() => grammar.sections.find(section => section.id === activeGrammarId.value) || grammar.sections[0])

const visibleWords = computed(() => onlyUnknown.value ? store.currentWords.filter(word => !store.isKnown(word.id)) : store.currentWords)

function itemKey(dataset, item) { return `${dataset.ns}:${dataset.activeId.value}|${item.word}` }
function activeItemGroup(dataset) { return dataset.data.groups.find(group => group.id === dataset.activeId.value) || dataset.data.groups[0] }
function totalItems(dataset) { return dataset.data.groups.reduce((sum, group) => sum + group.words.length, 0) }
function countKnownItems(dataset) {
  const keys = dataset.data.groups.flatMap(group => group.words.map(item => `${dataset.ns}:${group.id}|${item.word}`))
  return progress.countKnown(keys)
}
function groupKnownCount(dataset) {
  const group = activeItemGroup(dataset)
  return progress.countKnown(group.words.map(item => `${dataset.ns}:${group.id}|${item.word}`))
}

function grammarKey(index) { return `gra:${activeGrammarId.value}|${index}` }
const grammarSectionKnown = computed(() => progress.countKnown(activeGrammarSection.value.points.map((_, index) => `gra:${activeGrammarId.value}|${index}`)))
const grammarPointTotal = computed(() => grammar.sections.reduce((sum, section) => sum + section.points.length, 0))
const grammarKnownTotal = computed(() => progress.countKnown(grammar.sections.flatMap(section => section.points.map((_, index) => `gra:${section.id}|${index}`))))

// 统一自测引擎
const testOpen = ref(false)
const testTitle = ref('')
const testMarksMastery = ref(true)
const testQuestions = ref([])
const testAnswers = reactive({})
const testResult = ref(null)
const answeredCount = computed(() => testQuestions.value.filter(question => testAnswers[question.id] !== undefined).length)

function shuffle(list) {
  const arr = [...list]
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

function openTest(title, questions, marksMastery = true) {
  if (!questions.length) { ElMessage.warning('暂无可用的自测题'); return }
  testTitle.value = title
  testMarksMastery.value = marksMastery
  testQuestions.value = questions
  Object.keys(testAnswers).forEach(key => delete testAnswers[key])
  testResult.value = null
  testOpen.value = true
}

function submitTest() {
  if (answeredCount.value < testQuestions.value.length) return
  let correct = 0
  testQuestions.value.forEach(question => {
    if (testAnswers[question.id] === question.answer) {
      correct += 1
      if (question.onCorrect) question.onCorrect()
    } else if (question.onWrong) {
      question.onWrong()
    }
  })
  testResult.value = { correct, total: testQuestions.value.length }
}

function startVocabTest() {
  const pool = store.currentWords
  if (!pool.length) { ElMessage.warning('本组没有单词可测'); return }
  const questions = shuffle(pool).slice(0, Math.min(10, pool.length)).map(word => ({
    id: `v-${word.id}`,
    prompt: word.word,
    hint: word.phonetic,
    speak: true,
    options: shuffle([word.meaning, ...shuffle(store.words.filter(item => item.id !== word.id)).slice(0, 3).map(item => item.meaning)]),
    answer: word.meaning,
    onCorrect: () => { if (!store.isKnown(word.id)) store.toggleKnown(word.id) },
    onWrong: () => { if (store.isKnown(word.id)) store.toggleKnown(word.id) }
  }))
  openTest(`3500 第 ${store.currentBatch + 1} 组 · 词义自测`, questions)
}

function startItemTest(dataset) {
  const group = activeItemGroup(dataset)
  const allMeanings = dataset.data.groups.flatMap(item => item.words.map(word => word.meaning))
  const questions = shuffle(group.words).slice(0, Math.min(10, group.words.length)).map(item => ({
    id: `${dataset.ns}-${item.word}`,
    prompt: item.word,
    speak: true,
    options: shuffle([item.meaning, ...shuffle(allMeanings.filter(meaning => meaning !== item.meaning)).slice(0, 3)]),
    answer: item.meaning,
    onCorrect: () => { const key = `${dataset.ns}:${group.id}|${item.word}`; if (!progress.isKnown(key)) progress.toggle(key) },
    onWrong: () => { const key = `${dataset.ns}:${group.id}|${item.word}`; if (progress.isKnown(key)) progress.toggle(key) }
  }))
  openTest(`${group.short} · 释义自测`, questions)
}

function startGrammarTest() {
  const section = activeGrammarSection.value
  const questions = shuffle(section.quiz || []).map((item, index) => ({
    id: `gra-${section.id}-${index}`,
    prompt: item.stem,
    speak: /[A-Za-z]/.test(item.stem),
    options: shuffle(item.options),
    answer: item.answer
  }))
  openTest(`${section.short} · 语法自测`, questions, false)
}

// —— 语音朗读：等异步加载完成 + 按质量优选声音，避免 Chrome/Edge 选到沙哑的精简音 ——
let cachedVoices = []
function loadVoices() {
  cachedVoices = window.speechSynthesis?.getVoices() || []
}
if ('speechSynthesis' in window) {
  loadVoices()
  // getVoices() 首次常为空，声音列表异步就绪后会触发该事件
  window.speechSynthesis.onvoiceschanged = loadVoices
}

// 按优先级挑高质量英文声音；排除名字带 compact（精简/低质量）的
function pickBestVoice() {
  const voices = cachedVoices.length ? cachedVoices : (window.speechSynthesis?.getVoices() || [])
  const en = voices.filter(v => /^en[-_]?/i.test(v.lang))
  if (!en.length) return null
  const enUS = en.filter(v => /en[-_]?US/i.test(v.lang))
  const pool = enUS.length ? enUS : en
  const preferred = [
    /Google US English/i,                 // Chrome 自然音
    /Microsoft.*(Aria|Jenny|Guy|Natural)/i, // Edge 自然音
    /Samantha/i,                          // macOS Apple 优质音
    /Microsoft.*(Zira|David|Mark)/i
  ]
  for (const re of preferred) {
    const hit = pool.find(v => re.test(v.name) && !/compact/i.test(v.name))
    if (hit) return hit
  }
  return pool.find(v => !/compact/i.test(v.name)) || pool[0]
}

function speak(text) {
  if (!('speechSynthesis' in window)) { ElMessage.warning('当前浏览器不支持语音朗读'); return }
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'en-US'
  utterance.rate = 0.9
  const voice = pickBestVoice()
  if (voice) utterance.voice = voice
  window.speechSynthesis.speak(utterance)
}

function confirmReset() {
  ElMessageBox.confirm('将清空所有单词掌握记录，确定重置吗？', '重置背词进度', { type: 'warning' })
    .then(() => { store.resetProgress(); ElMessage.success('已重置背词进度') })
    .catch(() => {})
}
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}
.page-intro h2{color:var(--ink);font-size:1.7rem}
.page-intro p{margin-top:5px;color:var(--text-secondary);max-width:80ch}
.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}
.drill-tabs{margin-top:-4px}
:deep(.drill-tabs .el-tabs__item){font-size:.95rem;height:46px}
.tab-label{font-weight:700}
.drill-hero{display:grid;grid-template-columns:200px 1fr auto;gap:24px;align-items:center;padding:22px 26px;border:1px solid #d8e3f2;border-radius:20px;background:linear-gradient(145deg,#fff,#f2f7ff)}
.hero-score span,.hero-score small{display:block;color:var(--text-muted);font-size:.74rem}
.hero-score strong{display:block;color:var(--ink);font-size:2.6rem;line-height:1.05}
.hero-progress p{margin-top:12px;color:var(--text-secondary);font-size:.78rem}
.hero-reset{align-self:start}
.drill-toolbar{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-top:16px}
.toolbar-left,.toolbar-right{display:flex;align-items:center;gap:10px}
.batch-select{width:190px}
.word-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}
.word-card{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:15px 16px;border:1px solid var(--line);border-radius:14px;background:#fff;transition:.18s ease}
.word-card:hover{box-shadow:var(--shadow-sm)}
.word-card.known{background:#f4fbf7;border-color:#c9efdf}
.word-main{min-width:0;flex:1}
.word-top{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.word-top strong{color:var(--ink);font-size:1rem}
.speakable{cursor:pointer}
.speakable:hover{color:var(--primary)}
.speak-btn{height:24px;width:24px;padding:0;color:var(--primary)}
.phonetic{color:var(--text-muted);font-size:.76rem;font-style:italic}
.meaning{margin-top:5px;color:var(--text-secondary);font-size:.8rem;line-height:1.4}
.known-toggle{flex:0 0 auto}
.known-toggle.mini{height:26px;width:26px;padding:0;margin-left:auto}
.extra-bar{display:flex;align-items:center;gap:14px}
.extra-intro{flex:1}
.extra-progress{flex:0 0 auto;text-align:center;padding:8px 18px;border:1px solid var(--line);border-radius:12px;background:#fff}
.extra-progress small{display:block;color:var(--text-muted);font-size:.68rem}
.extra-progress strong{color:var(--ink);font-size:1.1rem}
.essential-nav{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.essential-nav button{padding:8px 16px;border:1px solid var(--line);border-radius:999px;color:var(--text-secondary);font-size:.82rem;font-weight:600;background:#fff;cursor:pointer;transition:.18s ease}
.essential-nav button:hover{border-color:#bfd4ff;color:var(--primary)}
.essential-nav button.active{color:#fff;border-color:var(--primary);background:var(--primary)}
.essential-group{margin-top:18px}
.group-head{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.group-head h3{color:var(--ink);font-size:1.05rem}
.group-head>span{color:var(--text-muted);font-size:.76rem}
.group-actions{margin-left:auto;display:flex;align-items:center;gap:10px}
.group-count{color:var(--text-muted);font-size:.74rem}
.essential-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.essential-card{padding:15px 16px;border:1px solid var(--line);border-radius:14px;background:#fff;transition:.18s ease}
.essential-card.known{background:#f4fbf7;border-color:#c9efdf}
.essential-top{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.essential-top strong{color:var(--ink);font-size:1rem}
.essential-card .meaning{margin:5px 0 9px}
.example{display:flex;align-items:center;gap:6px;padding:9px 11px;border-radius:10px;color:var(--primary-deep);font-size:.8rem;line-height:1.45;background:var(--primary-soft);cursor:pointer}
.example .el-icon{flex:0 0 auto;color:var(--primary)}
.grammar-list{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.grammar-card{padding:18px;border:1px solid var(--line);border-radius:14px;background:#fff;transition:.18s ease}
.grammar-card.known{background:#f4fbf7;border-color:#c9efdf}
.grammar-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.grammar-head h4{color:var(--ink);font-size:.96rem}
.grammar-explain{margin:8px 0 12px;color:var(--text-secondary);font-size:.82rem;line-height:1.5}
.grammar-examples{display:flex;flex-direction:column;gap:8px;list-style:none}
.grammar-examples li{padding:9px 12px;border-radius:10px;background:#f6f9fe}
.ex-en{display:flex;align-items:center;gap:6px;color:var(--ink);font-size:.84rem;cursor:pointer}
.ex-en .el-icon{flex:0 0 auto;color:var(--primary)}
.ex-en:hover{color:var(--primary)}
.ex-cn{display:block;margin-top:3px;padding-left:22px;color:var(--text-muted);font-size:.75rem}
.test-tip{margin-bottom:14px;color:var(--text-secondary);font-size:.82rem}
.test-question{padding:14px 0;border-top:1px solid var(--line)}
.test-question:first-of-type{border-top:0}
.test-q-head{display:flex;align-items:center;gap:9px;margin-bottom:10px;flex-wrap:wrap}
.q-order{width:24px;height:24px;display:grid;place-items:center;flex:0 0 auto;border-radius:7px;color:var(--primary);font-size:.7rem;font-weight:800;background:var(--primary-soft)}
.test-q-head strong{color:var(--ink);font-size:1rem}
.test-options{display:grid;grid-template-columns:1fr 1fr;gap:8px;width:100%}
:deep(.test-options .el-radio){width:100%;height:auto;min-height:40px;margin:0;padding:9px 12px;border-radius:10px}
:deep(.test-options .el-radio__label){white-space:normal;line-height:1.35;font-size:.78rem}
.test-result{text-align:center;padding:16px 8px}
.result-mark{width:58px;height:58px;display:grid;place-items:center;margin:0 auto 12px;border-radius:18px;font-size:28px}
.result-mark.full{color:var(--mint);background:var(--mint-soft)}
.result-mark.partial{color:#b77400;background:var(--accent-soft)}
.test-result h3{color:var(--ink);font-size:1.3rem}
.test-result p{margin-top:6px;color:var(--text-secondary);font-size:.82rem}
@media(max-width:1050px){.word-grid,.essential-grid,.grammar-list{grid-template-columns:repeat(2,1fr)}.drill-hero{grid-template-columns:1fr auto}}
@media(max-width:680px){.drill-hero{grid-template-columns:1fr}.hero-reset{justify-self:start}.word-grid,.essential-grid,.grammar-list{grid-template-columns:1fr}.test-options{grid-template-columns:1fr}.drill-toolbar{flex-direction:column;align-items:stretch}.toolbar-left,.toolbar-right{flex-wrap:wrap}.extra-bar{flex-direction:column;align-items:stretch}}
</style>
