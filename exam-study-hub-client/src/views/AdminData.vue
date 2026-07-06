<template>
  <div class="admin-data-page page-stack">
    <section class="page-intro">
      <div>
        <span class="section-kicker">系统管理</span>
        <h2>数据管理</h2>
        <p>查看招生数据、导入批次、题库质量和主数据覆盖情况。当前版本为只读运营台，避免误改正式数据。</p>
      </div>
      <el-button class="refresh-btn" :loading="loading" @click="refreshAll">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </section>

    <section class="stat-grid">
      <div v-for="stat in summary?.stats || []" :key="stat.key" class="stat-tile" :class="`tone-${stat.tone}`">
        <small>{{ stat.label }}</small>
        <strong>{{ stat.value }}</strong>
        <span>{{ stat.description || stat.key }}</span>
      </div>
    </section>

    <el-alert
      v-if="summary"
      :type="summary.validation.passed ? 'success' : 'error'"
      :title="summary.validation.passed ? '数据硬校验通过' : `数据硬校验发现 ${summary.validation.issues.length} 个问题`"
      :closable="false"
      show-icon
    />

    <el-tabs v-model="activeTab" class="data-tabs">
      <el-tab-pane label="院校数据" name="institutions">
        <el-alert
          class="scope-alert"
          type="info"
          title="本页按招生省份归档：招生省份表示院校出现在该省公开招生 / 征集计划中，院校所在地单独展示；省外院校不是脏数据。"
          :closable="false"
          show-icon
        />
        <section class="toolbar">
          <el-select v-model="institutionFilters.province" clearable placeholder="全部省份" class="filter-select" @change="reloadInstitutions">
            <el-option v-for="province in catalog?.provinces || []" :key="province.code" :label="province.name" :value="province.code" />
          </el-select>
          <el-input v-model="institutionFilters.keyword" clearable placeholder="搜索院校名称 / 代码" class="filter-input" @keyup.enter="reloadInstitutions">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-checkbox v-model="institutionFilters.issueOnly" @change="reloadInstitutions">只看有问题</el-checkbox>
          <el-button type="primary" plain @click="reloadInstitutions">查询</el-button>
        </section>

        <el-table :data="institutions.items" v-loading="institutionLoading" stripe class="data-table">
          <el-table-column label="院校 / 招生口径" min-width="280">
            <template #default="{ row }">
              <strong class="table-main">{{ row.name }}</strong>
              <div class="school-meta">
                <span>代码 {{ row.code }}</span>
                <span>招生省份：{{ row.province_name }}</span>
                <span>院校所在地：{{ row.city || '未填城市' }}</span>
                <el-tag v-if="row.city && !isLocalInstitution(row)" size="small" type="warning" effect="plain" class="location-tag">省外院校</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="参考线" width="130">
            <template #default="{ row }">
              <span>{{ row.latest_score != null ? `${row.latest_score} 分` : '—' }}</span>
              <small class="table-sub">{{ row.latest_score_year || '—' }} {{ row.latest_line_type || '' }}</small>
            </template>
          </el-table-column>
          <el-table-column label="专业计划" width="120">
            <template #default="{ row }">{{ row.plans_count }} 条 / {{ row.plan_major_count }} 专业</template>
          </el-table-column>
          <el-table-column label="数据状态" width="120">
            <template #default="{ row }">
              <el-tag :type="qualityTag(row.quality)" effect="plain">{{ row.quality }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="问题" min-width="180">
            <template #default="{ row }">
              <span v-if="!row.issues.length" class="muted">暂无</span>
              <el-tag v-for="issue in row.issues" v-else :key="issue" size="small" type="warning" effect="plain" class="issue-tag">{{ issue }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="来源" width="88" align="right">
            <template #default="{ row }">
              <a v-if="row.latest_source" :href="row.latest_source" target="_blank" rel="noopener" class="source-link">打开</a>
              <span v-else class="muted">—</span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-model:current-page="institutionFilters.page"
          v-model:page-size="institutionFilters.pageSize"
          class="pagination"
          layout="total, sizes, prev, pager, next"
          :page-sizes="[20, 30, 50, 100]"
          :total="institutions.total"
          @current-change="reloadInstitutions"
          @size-change="reloadInstitutions"
        />
      </el-tab-pane>

      <el-tab-pane label="导入批次" name="batches">
        <el-table :data="batches" v-loading="loading" stripe class="data-table">
          <el-table-column prop="data_type" label="数据类型" width="110" />
          <el-table-column label="省份 / 年度" width="130">
            <template #default="{ row }">{{ row.province_name }} · {{ row.year }}</template>
          </el-table-column>
          <el-table-column label="批次口径" min-width="170">
            <template #default="{ row }">
              <strong class="table-main">{{ row.line_type }}</strong>
              <small class="table-sub">{{ row.round || '未标注批次' }}</small>
            </template>
          </el-table-column>
          <el-table-column label="记录数" width="95">
            <template #default="{ row }">{{ row.records_count }}</template>
          </el-table-column>
          <el-table-column label="院校 / 专业" width="120">
            <template #default="{ row }">{{ row.institutions_count }} / {{ row.majors_count ?? '—' }}</template>
          </el-table-column>
          <el-table-column label="来源" min-width="180">
            <template #default="{ row }">
              <a v-if="row.source" :href="row.source" target="_blank" rel="noopener" class="source-link">{{ compactSource(row.source) }}</a>
              <span v-else class="muted">未记录来源</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="题库质量" name="questions">
        <section class="subject-grid">
          <div v-for="subject in questionQuality?.subjects || []" :key="subject.subject" class="subject-tile">
            <strong>{{ subject.subject }}</strong>
            <span class="subject-meta">{{ subject.topics_count }} 知识点 · {{ subject.questions_count }} 题</span>
            <el-tag class="subject-status" :type="subject.issue_count ? 'warning' : 'success'" effect="plain">{{ subject.issue_count ? `${subject.issue_count} 个问题` : '正常' }}</el-tag>
          </div>
        </section>
        <el-table :data="questionQuality?.issues || []" stripe class="data-table">
          <el-table-column prop="severity" label="级别" width="90">
            <template #default="{ row }"><el-tag :type="row.severity === 'error' ? 'danger' : 'warning'" effect="plain">{{ row.severity }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="area" label="位置" width="180" />
          <el-table-column prop="message" label="问题说明" min-width="260" />
        </el-table>
        <el-empty v-if="questionQuality && !questionQuality.issues.length" description="题库质量检查未发现问题" :image-size="72" />
      </el-tab-pane>

      <el-tab-pane label="主数据" name="catalog">
        <section class="catalog-overview">
          <div v-for="item in catalogOverview" :key="item.label" class="catalog-metric">
            <span>{{ item.label }}</span>
            <strong>{{ formatNumber(item.value) }}</strong>
            <small>{{ item.hint }}</small>
          </div>
        </section>

        <section class="catalog-section">
          <div class="catalog-section-head">
            <div>
              <h3>省份覆盖</h3>
              <p>按招生省份汇总数据规模，报名提示只保留影响报考判断的信息。</p>
            </div>
          </div>
          <div class="province-grid">
            <article v-for="province in catalog?.provinces || []" :key="province.code" class="province-panel">
              <header>
                <strong>{{ province.name }}</strong>
                <el-tag size="small" effect="plain">{{ province.control_scores_count }} 条省控线</el-tag>
              </header>
              <p>{{ province.note || '暂无报名提示' }}</p>
              <dl class="province-kpis">
                <div>
                  <dt>院校</dt>
                  <dd>{{ formatNumber(province.institutions_count) }}</dd>
                </div>
                <div>
                  <dt>参考线</dt>
                  <dd>{{ formatNumber(province.scores_count) }}</dd>
                </div>
                <div>
                  <dt>专业计划</dt>
                  <dd>{{ formatNumber(province.plans_count) }}</dd>
                </div>
              </dl>
            </article>
          </div>
        </section>

        <section class="catalog-section">
          <div class="catalog-section-head">
            <div>
              <h3>专业科类</h3>
              <p>先看科类和统考科目，再进入下方专业明细。</p>
            </div>
          </div>
          <div class="category-grid">
            <button
              v-for="category in catalog?.categories || []"
              :key="category.category"
              type="button"
              class="category-card"
              :class="{ 'is-active': catalogFilters.category === category.category }"
              @click="catalogFilters.category = catalogFilters.category === category.category ? '' : category.category"
            >
              <span class="category-card-top">
                <strong>{{ category.category }}</strong>
                <em>{{ category.majors_count }} 个专业</em>
              </span>
              <span class="subject-chip-list">
                <span v-for="subject in category.subjects" :key="subject" class="subject-chip">{{ subject }}</span>
              </span>
            </button>
          </div>
        </section>

        <section class="catalog-section">
          <div class="catalog-section-head catalog-section-head--with-tools">
            <div>
              <h3>专业明细</h3>
              <p>共 {{ filteredCatalogMajors.length }} 个专业，按科类分组展示，避免长表格连续滚动。</p>
            </div>
            <div class="catalog-toolbar">
              <el-select v-model="catalogFilters.category" clearable placeholder="全部科类" class="catalog-filter">
                <el-option v-for="category in catalog?.categories || []" :key="category.category" :label="category.category" :value="category.category" />
              </el-select>
              <el-input v-model="catalogFilters.keyword" clearable placeholder="搜索专业名称 / 代码 / 科目" class="catalog-search">
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </div>
          </div>
          <el-empty v-if="catalog && !groupedCatalogMajors.length" description="没有匹配的专业" :image-size="72" />
          <div v-else class="major-group-list">
            <section v-for="group in groupedCatalogMajors" :key="group.category" class="major-group">
              <header>
                <div>
                  <strong>{{ group.category }}</strong>
                  <span>{{ group.majors.length }} 个专业</span>
                </div>
                <div class="subject-chip-list">
                  <span v-for="subject in group.subjects" :key="subject" class="subject-chip">{{ subject }}</span>
                </div>
              </header>
              <div class="major-chip-grid">
                <span v-for="major in group.majors" :key="major.code" class="major-chip">
                  <strong>{{ major.name }}</strong>
                  <small>{{ major.code }}</small>
                </span>
              </div>
            </section>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="校验结果" name="validation">
        <el-table :data="summary?.validation.issues || []" stripe class="data-table">
          <el-table-column label="级别" width="90">
            <template #default="{ row }"><el-tag :type="row.severity === 'error' ? 'danger' : 'warning'" effect="plain">{{ row.severity }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="area" label="模块" width="150" />
          <el-table-column prop="message" label="校验信息" min-width="280" />
        </el-table>
        <el-empty v-if="summary && !summary.validation.issues.length" description="数据校验通过，未发现硬规则问题" :image-size="72" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { isCityInProvince } from '../data/regions'
import {
  getAdminCatalog,
  getAdminDataSummary,
  getAdminImportBatches,
  getAdminInstitutions,
  getAdminQuestionQuality,
} from '../api'

const activeTab = ref('institutions')
const loading = ref(false)
const institutionLoading = ref(false)
const summary = ref(null)
const batches = ref([])
const questionQuality = ref(null)
const catalog = ref(null)
const institutions = ref({ total: 0, items: [] })
const institutionFilters = reactive({
  province: '',
  keyword: '',
  issueOnly: false,
  page: 1,
  pageSize: 30,
})
const catalogFilters = reactive({
  category: '',
  keyword: '',
})

const catalogOverview = computed(() => {
  const provinces = catalog.value?.provinces || []
  const categories = catalog.value?.categories || []
  const majors = catalog.value?.majors || []
  return [
    {
      label: '接入省份',
      value: provinces.length,
      hint: provinces.map(item => item.name).join(' / ') || '暂无省份',
    },
    {
      label: '招生院校',
      value: provinces.reduce((sum, item) => sum + item.institutions_count, 0),
      hint: '按招生省份归档',
    },
    {
      label: '招生与分数',
      value: provinces.reduce((sum, item) => sum + item.scores_count + item.plans_count + item.control_scores_count, 0),
      hint: '参考线 / 计划 / 省控线',
    },
    {
      label: '专业体系',
      value: majors.length,
      hint: `${categories.length || 0} 个科类`,
    },
  ]
})

const filteredCatalogMajors = computed(() => {
  const keyword = catalogFilters.keyword.trim().toLowerCase()
  return (catalog.value?.majors || []).filter(major => {
    const matchesCategory = !catalogFilters.category || major.category === catalogFilters.category
    if (!matchesCategory) return false
    if (!keyword) return true
    return [
      major.code,
      major.name,
      major.category,
      ...(major.subjects || []),
    ].some(value => String(value).toLowerCase().includes(keyword))
  })
})

const groupedCatalogMajors = computed(() => {
  const categoryMap = new Map((catalog.value?.categories || []).map(item => [
    item.category,
    { category: item.category, subjects: item.subjects || [], majors: [] },
  ]))
  for (const major of filteredCatalogMajors.value) {
    if (!categoryMap.has(major.category)) {
      categoryMap.set(major.category, { category: major.category, subjects: major.subjects || [], majors: [] })
    }
    categoryMap.get(major.category).majors.push(major)
  }
  return [...categoryMap.values()].filter(group => group.majors.length)
})

function qualityTag(value) {
  if (value === '完整') return 'success'
  if (value === '可参考') return 'info'
  return 'warning'
}

function isLocalInstitution(row) {
  return Boolean(row?.city && isCityInProvince(row.province, row.city))
}

function compactSource(value) {
  if (!value) return ''
  try {
    const url = new URL(value)
    return url.hostname.replace(/^www\./, '') + url.pathname.slice(-24)
  } catch {
    return value.length > 32 ? `${value.slice(0, 30)}...` : value
  }
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('zh-CN')
}

async function reloadInstitutions() {
  institutionLoading.value = true
  try {
    institutions.value = await getAdminInstitutions({
      province: institutionFilters.province || undefined,
      keyword: institutionFilters.keyword || undefined,
      issue_only: institutionFilters.issueOnly,
      page: institutionFilters.page,
      page_size: institutionFilters.pageSize,
    })
  } catch (error) {
    ElMessage.error(error.message || '加载院校数据失败')
  } finally {
    institutionLoading.value = false
  }
}

async function refreshAll() {
  loading.value = true
  try {
    const [summaryData, batchData, questionData, catalogData] = await Promise.all([
      getAdminDataSummary(),
      getAdminImportBatches(),
      getAdminQuestionQuality(),
      getAdminCatalog(),
    ])
    summary.value = summaryData
    batches.value = batchData
    questionQuality.value = questionData
    catalog.value = catalogData
    await reloadInstitutions()
  } catch (error) {
    ElMessage.error(error.message || '加载数据管理信息失败')
  } finally {
    loading.value = false
  }
}

onMounted(refreshAll)
</script>

<style scoped lang="less" src="../styles/views/AdminData.less"></style>
