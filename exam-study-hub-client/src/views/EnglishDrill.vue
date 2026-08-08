<template>
  <div class="drill-page page-stack" :class="{ 'has-listen-player': listenActive, 'has-minimized-listen-player': listenActive && listenMinimized }">
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
            <el-select :model-value="store.currentBatch" filterable class="batch-select" @change="store.setBatch($event)">
              <el-option v-for="option in store.batchOptions" :key="option.value" :label="option.label" :value="option.value" />
            </el-select>
            <el-button :disabled="store.currentBatch === store.batchCount - 1" @click="store.setBatch(store.currentBatch + 1)">下一组<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button>
          </div>
          <div class="toolbar-right">
            <el-checkbox v-model="onlyUnknown" label="只看未掌握" border />
            <el-button :type="currentBatchAllKnown ? 'warning' : 'default'" plain @click="handleCurrentBatchMastery">
              <el-icon><Close v-if="currentBatchAllKnown" /><Check v-else /></el-icon>
              {{ currentBatchAllKnown ? '一键取消掌握' : '一键全部掌握' }}
            </el-button>
            <el-dropdown class="listen-mode-dropdown" split-button type="success" @click="startListening('loop')" @command="startListening">
              <el-icon><Headset /></el-icon>{{ listenActive && listenMode === 'loop' ? '重新循环本组' : '循环本组听读' }}
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="loop">循环本组听读</el-dropdown-item>
                  <el-dropdown-item command="all">全部单词听读</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="primary" @click="startVocabTest"><el-icon><EditPen /></el-icon>本组自测</el-button>
          </div>
        </section>

        <section class="word-grid">
          <article
            v-for="word in visibleWords"
            :key="word.id"
            class="word-card"
            :class="{ known: store.isKnown(word.id), listening: listenActive && activeListenWord?.id === word.id }"
          >
            <div class="word-main">
              <div class="word-top">
                <strong class="speakable" @click="speak(word.word)">{{ word.word }}</strong>
                <el-button class="speak-btn" text circle @click="speak(word.word)"><el-icon><VideoPlay /></el-icon></el-button>
                <el-tag v-if="word.tag" size="small" effect="plain">{{ word.tag }}</el-tag>
                <span v-if="word.phonetic" class="phonetic">/{{ word.phonetic }}/</span>
              </div>
              <p class="meaning">{{ word.meaning }}</p>
            </div>
            <el-button class="known-toggle" :type="store.isKnown(word.id) ? 'success' : 'default'" :plain="!store.isKnown(word.id)" circle :aria-label="store.isKnown(word.id) ? `取消 ${word.word} 掌握标记` : `标记 ${word.word} 已掌握`" :title="store.isKnown(word.id) ? '取消掌握标记' : '标记已掌握'" @click="toggleWordMastery(word.id)"><el-icon><Check /></el-icon></el-button>
          </article>
          <el-empty v-if="visibleWords.length === 0" description="本组单词都已掌握，进入下一组吧" :image-size="80" />
        </section>
      </el-tab-pane>

      <!-- Tab 2: 合并核心短语与日常短句，复用单词区的进度、工具栏和卡片布局 -->
      <el-tab-pane name="phrases">
        <template #label><span class="tab-label">常用短语</span></template>

        <section class="drill-hero phrase-hero">
          <div class="hero-score"><span>已掌握短语</span><strong>{{ phraseKnownCount }}</strong><small>/ {{ phraseTotal }} 条</small></div>
          <div class="hero-progress">
            <el-progress :percentage="phraseMasteryPercent" :stroke-width="14" :text-inside="true" />
            <p>{{ activePhraseDataset.data.intro }} 当前第 {{ phraseGroupIndex + 1 }} 组已掌握 {{ phraseGroupKnown }}/{{ activePhraseGroup.words.length }}。</p>
          </div>
          <div class="phrase-source-switch" role="group" aria-label="短语内容分类">
            <el-button :type="phraseSource === 'core' ? 'primary' : 'default'" :plain="phraseSource !== 'core'" @click="phraseSource = 'core'">核心短语</el-button>
            <el-button :type="phraseSource === 'daily' ? 'primary' : 'default'" :plain="phraseSource !== 'daily'" @click="phraseSource = 'daily'">日常短句</el-button>
          </div>
        </section>

        <section class="drill-toolbar">
          <div class="toolbar-left">
            <el-button :disabled="phraseGroupIndex === 0" @click="setPhraseGroup(phraseGroupIndex - 1)"><el-icon><ArrowLeft /></el-icon>上一组</el-button>
            <el-select :model-value="phraseGroupIndex" class="batch-select" @change="setPhraseGroup($event)">
              <el-option v-for="option in phraseGroupOptions" :key="option.value" :label="option.label" :value="option.value" />
            </el-select>
            <el-button :disabled="phraseGroupIndex === phraseGroupOptions.length - 1" @click="setPhraseGroup(phraseGroupIndex + 1)">下一组<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button>
          </div>
          <div class="toolbar-right">
            <el-checkbox v-model="onlyUnknownPhrases" label="只看未掌握" border />
            <el-button :type="phraseGroupAllKnown ? 'warning' : 'default'" plain @click="handlePhraseGroupMastery">
              <el-icon><Close v-if="phraseGroupAllKnown" /><Check v-else /></el-icon>
              {{ phraseGroupAllKnown ? '一键取消掌握' : '一键全部掌握' }}
            </el-button>
            <el-dropdown class="listen-mode-dropdown" split-button type="success" @click="startItemListening(activePhraseDataset, 'loop')" @command="startPhraseListenCommand">
              <el-icon><Headset /></el-icon>{{ listenActive && isListeningDataset(activePhraseDataset) && listenMode === 'loop' ? '重新循环本组' : '循环本组听读' }}
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="loop">循环本组听读</el-dropdown-item>
                  <el-dropdown-item command="all">全部当前分类听读</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="primary" @click="startItemTest(activePhraseDataset)"><el-icon><EditPen /></el-icon>本组自测</el-button>
          </div>
        </section>

        <section class="word-grid phrase-word-grid">
          <article
            v-for="item in visiblePhraseItems"
            :key="item.word"
            class="word-card phrase-word-card"
            :class="{ known: progress.isKnown(itemKey(activePhraseDataset, item)), listening: isListeningDataset(activePhraseDataset) && activeListenWord?.id === itemKey(activePhraseDataset, item) }"
          >
            <div class="word-main">
              <div class="word-top">
                <strong class="speakable" @click="speak(item.word)">{{ item.word }}</strong>
                <el-button class="speak-btn" text circle @click="speak(item.word)"><el-icon><VideoPlay /></el-icon></el-button>
                <el-tag v-if="item.tag" size="small" effect="plain">{{ item.tag }}</el-tag>
              </div>
              <p class="meaning">{{ item.meaning }}</p>
              <p v-if="item.example" class="example speakable" @click="speak(item.example)"><el-icon><VideoPlay /></el-icon>{{ item.example }}</p>
            </div>
            <el-button class="known-toggle" :type="progress.isKnown(itemKey(activePhraseDataset, item)) ? 'success' : 'default'" :plain="!progress.isKnown(itemKey(activePhraseDataset, item))" circle :aria-label="progress.isKnown(itemKey(activePhraseDataset, item)) ? `取消 ${item.word} 掌握标记` : `标记 ${item.word} 已掌握`" :title="progress.isKnown(itemKey(activePhraseDataset, item)) ? '取消掌握标记' : '标记已掌握'" @click="progress.toggle(itemKey(activePhraseDataset, item))"><el-icon><Check /></el-icon></el-button>
          </article>
          <el-empty v-if="visiblePhraseItems.length === 0" description="本组短语都已掌握，进入下一组吧" :image-size="80" />
        </section>
      </el-tab-pane>

      <!-- Tab 3: 造句基础 -->
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
              <el-dropdown v-if="dataset.listenable" split-button size="small" type="success" plain @click="startItemListening(dataset, 'loop')" @command="startItemListenCommand(dataset, $event)">
                <el-icon><Headset /></el-icon>{{ isListeningDataset(dataset) && listenMode === 'loop' ? '重新循环本组' : '循环听本组' }}
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="loop">循环本组听读</el-dropdown-item>
                    <el-dropdown-item command="all">全部短句听读</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button size="small" type="primary" plain @click="startItemTest(dataset)"><el-icon><EditPen /></el-icon>本组自测</el-button>
            </div>
          </div>
          <div class="essential-grid">
            <article v-for="item in activeItemGroup(dataset).words" :key="item.word" class="essential-card" :class="{ known: progress.isKnown(itemKey(dataset, item)), listening: isListeningDataset(dataset) && activeListenWord?.id === itemKey(dataset, item) }">
              <div class="essential-top">
                <strong class="speakable" @click="speak(item.word)">{{ item.word }}</strong>
                <el-button class="speak-btn" text circle @click="speak(item.word)"><el-icon><VideoPlay /></el-icon></el-button>
                <el-tag v-if="item.tag" size="small" effect="plain">{{ item.tag }}</el-tag>
                <el-button class="known-toggle mini" :type="progress.isKnown(itemKey(dataset, item)) ? 'success' : 'default'" :plain="!progress.isKnown(itemKey(dataset, item))" circle :aria-label="progress.isKnown(itemKey(dataset, item)) ? `取消 ${item.word} 掌握标记` : `标记 ${item.word} 已掌握`" :title="progress.isKnown(itemKey(dataset, item)) ? '取消掌握标记' : '标记已掌握'" @click="progress.toggle(itemKey(dataset, item))"><el-icon><Check /></el-icon></el-button>
              </div>
              <p class="meaning">{{ item.meaning }}</p>
              <p v-if="item.example" class="example speakable" @click="speak(item.example)"><el-icon><VideoPlay /></el-icon>{{ item.example }}</p>
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
                <el-button class="known-toggle mini" :type="progress.isKnown(grammarKey(index)) ? 'success' : 'default'" :plain="!progress.isKnown(grammarKey(index))" circle :aria-label="progress.isKnown(grammarKey(index)) ? `取消 ${point.title} 掌握标记` : `标记 ${point.title} 已掌握`" :title="progress.isKnown(grammarKey(index)) ? '取消掌握标记' : '标记已掌握'" @click="progress.toggle(grammarKey(index))"><el-icon><Check /></el-icon></el-button>
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

    <Transition name="listen-player">
      <section v-if="listenActive" class="listen-player" :class="{ 'is-minimized': listenMinimized }" role="region" aria-label="听词模式播放器">
        <template v-if="!listenMinimized">
          <el-button class="listen-minimize" circle text aria-label="缩小听写窗" title="缩小听写窗" @click="listenMinimized = true">
            <span class="listen-minimize-mark" aria-hidden="true">−</span>
          </el-button>
          <el-button class="listen-dismiss" circle text aria-label="结束听词" title="结束听词" @click="stopListening(true)">
            <el-icon><Close /></el-icon>
          </el-button>

          <div class="listen-summary" aria-live="polite">
            <div class="listen-heading">
              <span class="listen-status"><el-icon><Headset /></el-icon>{{ listenPaused ? '已暂停' : listenPhase }}</span>
              <div class="listen-word">
                <strong>{{ activeListenWord?.word }}</strong>
                <span v-if="activeListenWord?.phonetic">/{{ activeListenWord.phonetic }}/</span>
              </div>
            </div>
            <p>{{ activeListenWord?.meaning }}</p>
          </div>

          <div class="listen-progress">
            <span>{{ listenMode === 'loop' ? '循环本组' : '全部听读' }} · 第 {{ listenIndex + 1 }} / {{ listenQueue.length }} 个</span>
            <el-progress :percentage="listenPercent" :show-text="false" :stroke-width="6" />
          </div>

          <div class="listen-controls">
            <el-button circle plain :disabled="listenQueue.length < 2" aria-label="上一个单词" title="上一个单词" @click="previousListenWord">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <el-button class="listen-toggle" circle type="primary" :aria-label="listenPaused ? '继续播放' : '暂停播放'" :title="listenPaused ? '继续播放' : '暂停播放'" @click="toggleListenPause">
              <el-icon><VideoPlay v-if="listenPaused" /><VideoPause v-else /></el-icon>
            </el-button>
            <el-button circle plain :disabled="listenQueue.length < 2" aria-label="下一个单词" title="下一个单词" @click="nextListenWord">
              <el-icon><ArrowRight /></el-icon>
            </el-button>
            <el-button circle plain aria-label="重读当前单词" title="重读当前单词" @click="replayListenWord">
              <el-icon><RefreshRight /></el-icon>
            </el-button>
          </div>

          <div class="listen-options">
            <el-select v-model="listenRate" class="listen-rate" aria-label="朗读语速" @change="handleListenRateChange">
              <el-option label="0.8×" :value="0.8" />
              <el-option label="1.0×" :value="1" />
              <el-option label="1.2×" :value="1.2" />
            </el-select>
            <el-radio-group v-model="listenMode" class="listen-mode-switch" size="small" aria-label="听读范围" @change="handleListenModeChange">
              <el-radio-button value="loop">循环本组</el-radio-button>
              <el-radio-button value="all">全部听读</el-radio-button>
            </el-radio-group>
            <el-checkbox v-if="listenSource === 'words'" v-model="listenOnlyUnknown" label="仅未掌握" border @change="rebuildListenQueue" />
          </div>
        </template>

        <template v-else>
          <div class="listen-mini-summary" aria-live="polite">
            <span class="listen-mini-status"><el-icon><Headset /></el-icon>{{ listenPaused ? '已暂停' : listenPhase }}</span>
            <strong>{{ activeListenWord?.word }}</strong>
          </div>
          <div class="listen-mini-actions">
            <el-button class="listen-mini-toggle" circle type="primary" :aria-label="listenPaused ? '继续播放' : '暂停播放'" :title="listenPaused ? '继续播放' : '暂停播放'" @click="toggleListenPause">
              <el-icon><VideoPlay v-if="listenPaused" /><VideoPause v-else /></el-icon>
            </el-button>
            <el-button circle plain aria-label="展开听写窗" title="展开听写窗" @click="listenMinimized = false">
              <el-icon class="listen-expand-icon"><ArrowDown /></el-icon>
            </el-button>
            <el-button circle text aria-label="结束听词" title="结束听词" @click="stopListening(true)">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </template>
      </section>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useVocabularyStore } from '../stores/vocabulary'
import { useEnglishProgressStore } from '../stores/englishProgress'
import essentials from '../../docs/EnglishEssentials.json'
import phrases from '../../docs/EnglishPhrases.json'
import commonPhrases from '../../docs/EnglishCommonPhrases.json'
import grammar from '../../docs/EnglishGrammar.json'

const store = useVocabularyStore()
const progress = useEnglishProgressStore()
const activeTab = ref('words')
const onlyUnknown = ref(false)
const phraseSource = ref('core')
const onlyUnknownPhrases = ref(false)

// 造句基础沿用知识卡片；两类短语在「常用短语」标签内统一呈现。
const itemDatasets = [
  { ns: 'essentials', tabLabel: '造句基础', data: essentials, activeId: ref(essentials.groups[0].id) }
]
const phraseDatasets = {
  core: { ns: 'phrases', data: phrases, activeId: ref(phrases.groups[0].id) },
  daily: { ns: 'commonPhrases', data: commonPhrases, activeId: ref(commonPhrases.groups[0].id) }
}
const activePhraseDataset = computed(() => phraseDatasets[phraseSource.value])
const activePhraseGroup = computed(() => activeItemGroup(activePhraseDataset.value))
const phraseTotal = computed(() => totalItems(activePhraseDataset.value))
const phraseKnownCount = computed(() => countKnownItems(activePhraseDataset.value))
const phraseMasteryPercent = computed(() => phraseTotal.value ? Math.round(phraseKnownCount.value / phraseTotal.value * 100) : 0)
const phraseGroupIndex = computed(() => Math.max(0, activePhraseDataset.value.data.groups.findIndex(group => group.id === activePhraseDataset.value.activeId.value)))
const phraseGroupOptions = computed(() => activePhraseDataset.value.data.groups.map((group, index) => ({ value: index, label: `第 ${index + 1} 组 · ${group.short}` })))
const phraseGroupKnown = computed(() => groupKnownCount(activePhraseDataset.value))
const phraseGroupAllKnown = computed(() => activePhraseGroup.value.words.length > 0 && phraseGroupKnown.value === activePhraseGroup.value.words.length)
const visiblePhraseItems = computed(() => onlyUnknownPhrases.value ? activePhraseGroup.value.words.filter(item => !progress.isKnown(itemKey(activePhraseDataset.value, item))) : activePhraseGroup.value.words)
const activeGrammarId = ref(grammar.sections[0].id)
const activeGrammarSection = computed(() => grammar.sections.find(section => section.id === activeGrammarId.value) || grammar.sections[0])

const visibleWords = computed(() => onlyUnknown.value ? store.currentWords.filter(word => !store.isKnown(word.id)) : store.currentWords)
const currentBatchAllKnown = computed(() => store.currentWords.length > 0 && store.currentBatchKnown === store.currentWords.length)

// 听词模式：对当前组创建一份播放快照，避免掌握状态变化打乱正在播放的顺序。
const listenActive = ref(false)
const listenPaused = ref(false)
const listenPhase = ref('准备播放')
const listenQueue = ref([])
const listenIndex = ref(0)
const listenRate = ref(1)
const listenOnlyUnknown = ref(false)
const listenSource = ref(null)
const listenMode = ref('loop')
const listenGroupId = ref(null)
const listenMinimized = ref(false)
const activeListenWord = computed(() => listenQueue.value[listenIndex.value] || null)
const listenPercent = computed(() => listenQueue.value.length ? Math.round((listenIndex.value + 1) / listenQueue.value.length * 100) : 0)

let listenRunId = 0
let listenTimer = null

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
function isListeningDataset(dataset) { return listenActive.value && listenSource.value === dataset.ns }

function setPhraseGroup(index) {
  const groups = activePhraseDataset.value.data.groups
  const safeIndex = Math.max(0, Math.min(groups.length - 1, Number(index)))
  activePhraseDataset.value.activeId.value = groups[safeIndex].id
}

function handlePhraseGroupMastery() {
  const dataset = activePhraseDataset.value
  const shouldMarkKnown = !phraseGroupAllKnown.value
  activePhraseGroup.value.words.forEach(item => {
    const key = itemKey(dataset, item)
    if (progress.isKnown(key) !== shouldMarkKnown) progress.toggle(key)
  })
  ElMessage.success(shouldMarkKnown ? '已标记本组全部短语为已掌握' : '已取消本组全部掌握标记')
}

function startPhraseListenCommand(mode) {
  startItemListening(activePhraseDataset.value, mode)
}

function toggleWordMastery(id) {
  store.toggleKnown(id)
}

function handleCurrentBatchMastery() {
  if (currentBatchAllKnown.value) {
    store.markCurrentBatch(false)
    ElMessage.success('已取消本组全部掌握标记')
    return
  }

  store.markCurrentBatch(true)
  ElMessage.success('已标记本组全部单词为已掌握')
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
  window.speechSynthesis.addEventListener('voiceschanged', loadVoices)
}

function pickBestEnglishVoice() {
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

function pickBestChineseVoice() {
  const voices = cachedVoices.length ? cachedVoices : (window.speechSynthesis?.getVoices() || [])
  const zh = voices.filter(v => /^zh[-_]?/i.test(v.lang))
  if (!zh.length) return null
  const mainland = zh.filter(v => /zh[-_]?(CN|Hans)/i.test(v.lang))
  const pool = mainland.length ? mainland : zh
  const preferred = [
    /Google.*(普通话|Mandarin|Chinese)/i,
    /Microsoft.*(Xiaoxiao|Yunxi|Natural)/i,
    /Tingting/i,
    /Meijia/i
  ]
  for (const re of preferred) {
    const hit = pool.find(v => re.test(v.name) && !/compact/i.test(v.name))
    if (hit) return hit
  }
  return pool.find(v => !/compact/i.test(v.name)) || pool[0]
}

function speak(text) {
  if (!('speechSynthesis' in window)) { ElMessage.warning('当前浏览器不支持语音朗读'); return }
  if (listenActive.value && !listenPaused.value) pauseListening()
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'en-US'
  utterance.rate = 0.9
  const voice = pickBestEnglishVoice()
  if (voice) utterance.voice = voice
  window.speechSynthesis.speak(utterance)
}

function clearListenSpeech() {
  listenRunId += 1
  if (listenTimer) {
    window.clearTimeout(listenTimer)
    listenTimer = null
  }
  window.speechSynthesis?.cancel()
}

function scheduleListenStep(callback, delay, runId) {
  listenTimer = window.setTimeout(() => {
    listenTimer = null
    if (listenActive.value && !listenPaused.value && runId === listenRunId) callback()
  }, delay)
}

function speakListenSegment(text, language, voice, onComplete, runId) {
  if (!text || runId !== listenRunId) { onComplete(); return }
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = language
  utterance.rate = listenRate.value
  if (voice) utterance.voice = voice
  utterance.onend = () => {
    if (runId === listenRunId) onComplete()
  }
  utterance.onerror = event => {
    if (runId === listenRunId && event.error !== 'canceled' && event.error !== 'interrupted') onComplete()
  }
  window.speechSynthesis.speak(utterance)
}

function playActiveListenWord() {
  if (!listenActive.value || listenPaused.value || !activeListenWord.value) return
  clearListenSpeech()
  const runId = listenRunId
  const word = activeListenWord.value
  listenPhase.value = '正在读英文'
  speakListenSegment(word.word, 'en-US', pickBestEnglishVoice(), () => {
    scheduleListenStep(() => {
      listenPhase.value = '正在读中文'
      speakListenSegment(word.meaning, 'zh-CN', pickBestChineseVoice(), () => {
        scheduleListenStep(advanceListenWord, 1500, runId)
      }, runId)
    }, 200, runId)
  }, runId)
}

function finishListening() {
  if (listenMode.value === 'loop' && listenQueue.value.length) {
    clearListenSpeech()
    listenIndex.value = 0
    listenPhase.value = '开始下一轮'
    const runId = listenRunId
    scheduleListenStep(playActiveListenWord, 650, runId)
    return
  }
  clearListenSpeech()
  listenActive.value = false
  listenPaused.value = false
  listenPhase.value = '播放完成'
  ElMessage.success(listenSource.value === 'words' ? '本组单词已播放完成' : '本组短语已播放完成')
  listenSource.value = null
}

function advanceListenWord() {
  if (listenIndex.value >= listenQueue.value.length - 1) {
    finishListening()
    return
  }
  listenIndex.value += 1
  playActiveListenWord()
}

function startListening(mode = 'loop') {
  if (!('speechSynthesis' in window)) { ElMessage.warning('当前浏览器不支持语音朗读'); return }
  if (onlyUnknown.value) listenOnlyUnknown.value = true
  const sourceWords = mode === 'all' ? store.words : store.currentWords
  const pool = listenOnlyUnknown.value ? sourceWords.filter(word => !store.isKnown(word.id)) : sourceWords
  if (!pool.length) { ElMessage.warning('当前组没有可播放的单词'); return }
  startListenQueue(pool, 'words', mode)
}

function startItemListening(dataset, mode = 'loop', groupId = dataset.activeId.value) {
  if (!('speechSynthesis' in window)) { ElMessage.warning('当前浏览器不支持语音朗读'); return }
  const groups = mode === 'all' ? dataset.data.groups : dataset.data.groups.filter(group => group.id === groupId)
  const pool = groups.flatMap(group => group.words.map(item => ({ ...item, id: `${dataset.ns}:${group.id}|${item.word}` })))
  if (!pool.length) { ElMessage.warning('本组没有可播放的短语'); return }
  startListenQueue(pool, dataset.ns, mode, groupId)
}

function startItemListenCommand(dataset, mode) {
  startItemListening(dataset, mode)
}

function startListenQueue(pool, source, mode = 'loop', groupId = null) {
  clearListenSpeech()
  listenQueue.value = [...pool]
  listenIndex.value = 0
  listenSource.value = source
  listenMode.value = mode
  listenGroupId.value = groupId
  listenMinimized.value = false
  listenActive.value = true
  listenPaused.value = false
  playActiveListenWord()
}

function pauseListening() {
  if (!listenActive.value) return
  clearListenSpeech()
  listenPaused.value = true
  listenPhase.value = '已暂停'
}

function resumeListening() {
  if (!listenActive.value) return
  listenPaused.value = false
  playActiveListenWord()
}

function toggleListenPause() {
  if (listenPaused.value) resumeListening()
  else pauseListening()
}

function previousListenWord() {
  if (listenQueue.value.length < 2) return
  listenIndex.value = (listenIndex.value - 1 + listenQueue.value.length) % listenQueue.value.length
  listenPaused.value = false
  playActiveListenWord()
}

function nextListenWord() {
  if (listenQueue.value.length < 2) return
  listenIndex.value = (listenIndex.value + 1) % listenQueue.value.length
  listenPaused.value = false
  playActiveListenWord()
}

function replayListenWord() {
  listenPaused.value = false
  playActiveListenWord()
}

function handleListenRateChange() {
  if (listenActive.value && !listenPaused.value) playActiveListenWord()
}

function handleListenModeChange(mode) {
  if (!listenActive.value) return
  if (listenSource.value === 'words') {
    startListening(mode)
    return
  }
  const dataset = itemDatasets.find(item => item.ns === listenSource.value)
  if (dataset) startItemListening(dataset, mode, listenGroupId.value)
}

function rebuildListenQueue() {
  if (!listenActive.value || listenSource.value !== 'words') return
  const currentId = activeListenWord.value?.id
  const sourceWords = listenMode.value === 'all' ? store.words : store.currentWords
  const nextQueue = listenOnlyUnknown.value ? sourceWords.filter(word => !store.isKnown(word.id)) : sourceWords
  if (!nextQueue.length) {
    stopListening()
    ElMessage.info('当前组没有未掌握单词')
    return
  }
  listenQueue.value = [...nextQueue]
  const currentIndex = nextQueue.findIndex(word => word.id === currentId)
  listenIndex.value = currentIndex >= 0 ? currentIndex : 0
  listenPaused.value = false
  playActiveListenWord()
}

function stopListening(showMessage = false) {
  clearListenSpeech()
  listenActive.value = false
  listenPaused.value = false
  listenQueue.value = []
  listenIndex.value = 0
  listenSource.value = null
  listenGroupId.value = null
  listenMinimized.value = false
  listenPhase.value = '准备播放'
  if (showMessage) ElMessage.info('已结束听词模式')
}

watch(() => store.currentBatch, () => {
  if (listenActive.value && listenSource.value === 'words' && listenMode.value === 'loop') {
    stopListening()
    ElMessage.info('已切换词组，听词模式已结束')
  }
})

watch(activeTab, tab => {
  if (listenActive.value && tab !== listenSource.value) stopListening()
})

watch(phraseSource, () => {
  if (listenActive.value && ['phrases', 'commonPhrases'].includes(listenSource.value)) stopListening()
  onlyUnknownPhrases.value = false
})

onBeforeUnmount(() => {
  clearListenSpeech()
  window.speechSynthesis?.removeEventListener('voiceschanged', loadVoices)
})

function confirmReset() {
  ElMessageBox.confirm('将清空所有单词掌握记录，确定重置吗？', '重置背词进度', { type: 'warning' })
    .then(() => { store.resetProgress(); ElMessage.success('已重置背词进度') })
    .catch(() => {})
}
</script>

<style scoped lang="less" src="../styles/views/EnglishDrill.less"></style>
