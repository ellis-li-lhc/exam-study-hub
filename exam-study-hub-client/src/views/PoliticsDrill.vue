<template>
  <div class="politics-page page-stack">
    <section class="page-intro">
      <div>
        <span class="section-kicker">政治特训</span>
        <h2>政治知识点速记 + 简答背诵</h2>
        <p>盖住答案先回忆，再揭晓核对，掌握了就标记。{{ bank.note }}</p>
      </div>
      <el-tag effect="plain">已掌握 {{ totalKnown }} / {{ totalCount }}</el-tag>
    </section>

    <el-tabs v-model="activeTab" class="drill-tabs">
      <!-- Tab 1: 知识点速记 -->
      <el-tab-pane name="memory">
        <template #label><span class="tab-label">知识点速记 · {{ bank.memory.length }}</span></template>

        <div class="toolbar">
          <el-select v-model="category" size="default" class="cat-select">
            <el-option v-for="c in memCategories" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
          <el-select v-model="currentBatch" size="default" class="batch-select">
            <el-option v-for="opt in batchOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <div class="toolbar-right">
            <el-checkbox v-model="onlyUnknown">只看未掌握</el-checkbox>
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
              class="mark-btn" :type="progress.isKnown(card.key) ? 'success' : 'default'"
              :plain="!progress.isKnown(card.key)" circle @click="progress.toggle(card.key)"
            ><el-icon><Check /></el-icon></el-button>
          </article>
          <el-empty v-if="!visibleCards.length" description="本组已全部掌握，切换分组或取消筛选" :image-size="64" />
        </div>

        <div class="pager">
          <el-button :disabled="currentBatch === 0" @click="currentBatch--">上一组</el-button>
          <span>第 {{ currentBatch + 1 }} / {{ batchCount }} 组</span>
          <el-button :disabled="currentBatch >= batchCount - 1" @click="currentBatch++">下一组</el-button>
        </div>
      </el-tab-pane>

      <!-- Tab 2: 简答题 -->
      <el-tab-pane name="essay">
        <template #label><span class="tab-label">简答题 · {{ bank.essay.length }}</span></template>
        <p class="essay-tip">简答题不机判分，按参考答案自评：背得出要点就标记掌握。</p>
        <el-select v-model="essayCategory" size="default" class="cat-select essay-cat">
          <el-option v-for="c in essayCategories" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
        <el-collapse class="essay-list">
          <el-collapse-item v-for="item in filteredEssays" :key="item.idx" :name="item.idx">
            <template #title>
              <span class="essay-title" :class="{ known: progress.isKnown(essayKey(item.idx)) }">
                <span class="essay-no">{{ item.idx + 1 }}</span>
                <span class="essay-q">{{ item.q }}</span>
                <el-icon v-if="progress.isKnown(essayKey(item.idx))" class="essay-done"><CircleCheck /></el-icon>
              </span>
            </template>
            <div class="essay-answer">{{ item.a }}</div>
            <div class="essay-foot">
              <el-button
                size="small" :type="progress.isKnown(essayKey(item.idx)) ? 'success' : 'primary'"
                :plain="!progress.isKnown(essayKey(item.idx))" round @click="progress.toggle(essayKey(item.idx))"
              ><el-icon><Check /></el-icon>{{ progress.isKnown(essayKey(item.idx)) ? '已掌握' : '标记掌握' }}</el-button>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useEnglishProgressStore } from '../stores/englishProgress'
import bank from '../../docs/PoliticsKnowledge.json'

const progress = useEnglishProgressStore()
const activeTab = ref('memory')
const BATCH_SIZE = 20
const currentBatch = ref(0)
const onlyUnknown = ref(false)
const showAll = ref(false)
const revealed = ref(new Set())
const category = ref('all')

const memKey = i => `polm-${i}`
const essayKey = i => `pole-${i}`

const memoryCards = computed(() => bank.memory.map((item, i) => ({ ...item, key: memKey(i), no: i + 1 })))

// 出现过的板块（按固定顺序），加上「全部」
const CATEGORY_ORDER = ['马克思主义哲学', '毛泽东思想与中国特色社会主义', '时政与综合']
function buildCategoryOptions(items) {
  const present = CATEGORY_ORDER.filter(c => items.some(it => it.category === c))
  return [{ value: 'all', label: `全部 · ${items.length}` },
    ...present.map(c => ({ value: c, label: `${c} · ${items.filter(it => it.category === c).length}` }))]
}
const memCategories = computed(() => buildCategoryOptions(bank.memory))

// 先按板块过滤，再分页
const categoryCards = computed(() => category.value === 'all'
  ? memoryCards.value
  : memoryCards.value.filter(c => c.category === category.value))
const batchCount = computed(() => Math.max(1, Math.ceil(categoryCards.value.length / BATCH_SIZE)))
const batchOptions = computed(() => Array.from({ length: batchCount.value }, (_, i) => {
  const start = i * BATCH_SIZE + 1
  const end = Math.min((i + 1) * BATCH_SIZE, categoryCards.value.length)
  return { value: i, label: `第 ${i + 1} 组 · ${start}-${end}` }
}))
const currentCards = computed(() => categoryCards.value.slice(currentBatch.value * BATCH_SIZE, currentBatch.value * BATCH_SIZE + BATCH_SIZE))
const visibleCards = computed(() => onlyUnknown.value ? currentCards.value.filter(c => !progress.isKnown(c.key)) : currentCards.value)

// 切换板块后回到第一组
watch(category, () => { currentBatch.value = 0 })

// 简答题按板块过滤
const essayCategory = ref('all')
const essayCategories = computed(() => buildCategoryOptions(bank.essay))
const filteredEssays = computed(() => bank.essay
  .map((item, i) => ({ ...item, idx: i }))
  .filter(item => essayCategory.value === 'all' || item.category === essayCategory.value))

const allMemKeys = computed(() => memoryCards.value.map(c => c.key))
const allEssayKeys = computed(() => bank.essay.map((_, i) => essayKey(i)))
const totalCount = computed(() => bank.memory.length + bank.essay.length)
const totalKnown = computed(() => progress.countKnown(allMemKeys.value) + progress.countKnown(allEssayKeys.value))

function reveal(key) {
  const next = new Set(revealed.value)
  next.add(key)
  revealed.value = next
}

function markBatch(known) {
  progress.markMany(currentCards.value.map(c => c.key), known)
}
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:16px}
.page-intro{display:flex;align-items:flex-start;justify-content:space-between}
.page-intro h2{color:var(--ink);font-size:1.6rem}.page-intro p{margin-top:5px;color:var(--text-secondary);font-size:.82rem;max-width:720px}
.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}
.tab-label{font-size:.9rem}
.toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px;flex-wrap:wrap}
.batch-select{width:220px}
.cat-select{width:240px}.essay-cat{margin-bottom:12px}
.toolbar-right{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.mem-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.mem-card{display:flex;gap:10px;padding:15px 16px;border:1px solid var(--line);border-radius:14px;background:#fff;transition:box-shadow .18s,border-color .18s}
.mem-card:hover{box-shadow:0 6px 16px rgba(37,99,235,.07)}
.mem-card.known{border-color:#bfe8cf;background:#f6fffb}
.mem-no{width:26px;height:26px;display:grid;place-items:center;flex:0 0 auto;border-radius:8px;color:var(--primary);font-size:.66rem;font-weight:800;background:var(--primary-soft)}
.mem-card.known .mem-no{color:#fff;background:var(--mint)}
.mem-body{flex:1;min-width:0}
.mem-q{color:var(--ink);font-size:.86rem;line-height:1.55}
.mem-a{margin-top:10px;padding:10px 12px;border-radius:10px;background:#eef7f2;color:#15795a;font-size:.84rem;line-height:1.6;font-weight:600}
.mark-btn{flex:0 0 auto;align-self:flex-start}
.pager{display:flex;align-items:center;justify-content:center;gap:16px;margin-top:16px;color:var(--text-secondary);font-size:.8rem}
.essay-tip{margin:2px 0 12px;color:var(--text-muted);font-size:.8rem}
.essay-list{border:0}
:deep(.essay-list){--el-collapse-border-color:transparent}
:deep(.essay-list .el-collapse-item){margin-bottom:10px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff;transition:box-shadow .18s}
:deep(.essay-list .el-collapse-item.is-active){box-shadow:0 6px 18px rgba(37,99,235,.08);border-color:#bcd3f7}
:deep(.essay-list .el-collapse-item__header){height:auto;min-height:56px;padding:14px 16px;border-bottom:0;line-height:1.5}
:deep(.essay-list .el-collapse-item__wrap){border-bottom:0}
:deep(.essay-list .el-collapse-item__content){padding:0 16px 16px}
.essay-title{display:flex;align-items:center;gap:10px;width:100%;color:var(--ink);font-size:.9rem;font-weight:600}
.essay-no{width:26px;height:26px;display:grid;place-items:center;flex:0 0 auto;border-radius:8px;color:var(--primary);font-size:.7rem;font-weight:800;background:var(--primary-soft)}
.essay-q{flex:1;min-width:0}
.essay-title.known .essay-no{color:#fff;background:var(--mint)}
.essay-done{color:#15a05a;flex:0 0 auto}
.essay-answer{white-space:pre-wrap;padding:14px 16px;border-radius:12px;background:#f6f8fc;color:var(--text-secondary);font-size:.82rem;line-height:1.8}
.essay-foot{display:flex;justify-content:flex-end;margin-top:12px}
@media(max-width:820px){.mem-grid{grid-template-columns:1fr}}
</style>
