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
          <el-table-column label="院校" min-width="210">
            <template #default="{ row }">
              <strong class="table-main">{{ row.name }}</strong>
              <small class="table-sub">{{ row.code }} · {{ row.province_name }} · {{ row.city || '未填城市' }}</small>
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
            <span>{{ subject.topics_count }} 知识点 · {{ subject.questions_count }} 题</span>
            <el-tag :type="subject.issue_count ? 'warning' : 'success'" effect="plain">{{ subject.issue_count ? `${subject.issue_count} 个问题` : '正常' }}</el-tag>
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
        <section class="catalog-layout">
          <div>
            <h3>省份覆盖</h3>
            <el-table :data="catalog?.provinces || []" stripe class="data-table compact">
              <el-table-column prop="name" label="省份" width="90" />
              <el-table-column prop="institutions_count" label="院校" width="78" />
              <el-table-column prop="scores_count" label="参考线" width="86" />
              <el-table-column prop="plans_count" label="计划" width="78" />
              <el-table-column prop="note" label="报名提示" min-width="160" />
            </el-table>
          </div>
          <div>
            <h3>专业科类</h3>
            <el-table :data="catalog?.categories || []" stripe class="data-table compact">
              <el-table-column prop="category" label="科类" width="120" />
              <el-table-column prop="majors_count" label="专业数" width="86" />
              <el-table-column label="统考科目" min-width="180">
                <template #default="{ row }">{{ row.subjects.join('、') }}</template>
              </el-table-column>
            </el-table>
          </div>
        </section>
        <el-table :data="catalog?.majors || []" stripe class="data-table majors-table">
          <el-table-column prop="code" label="专业代码" width="160" />
          <el-table-column prop="name" label="专业名称" min-width="160" />
          <el-table-column prop="category" label="科类" width="130" />
          <el-table-column label="统考科目" min-width="190">
            <template #default="{ row }">{{ row.subjects.join('、') }}</template>
          </el-table-column>
        </el-table>
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
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

function qualityTag(value) {
  if (value === '完整') return 'success'
  if (value === '可参考') return 'info'
  return 'warning'
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

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}.page-intro{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.page-intro h2{color:var(--ink);font-size:1.7rem}.page-intro p{margin-top:5px;color:var(--text-secondary);font-size:.85rem;line-height:1.7}.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:900;letter-spacing:.08em}.refresh-btn{min-width:84px}.stat-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}.stat-tile{min-height:92px;padding:14px;border:1px solid var(--line);border-radius:var(--radius-md);background:#fff;box-shadow:var(--shadow-xs)}.stat-tile small,.stat-tile span{display:block;color:var(--text-muted);font-size:.72rem}.stat-tile strong{display:block;margin:8px 0 2px;color:var(--ink);font-size:1.8rem;line-height:1;font-variant-numeric:tabular-nums}.tone-blue{border-color:#c8d9f5}.tone-green{border-color:#bfe7cf}.tone-amber{border-color:#f7dca4}.data-tabs{padding:14px 18px 18px;border:1px solid var(--line);border-radius:var(--radius-lg);background:#fff;box-shadow:var(--shadow-xs)}.toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:14px}.filter-select{width:150px}.filter-input{width:260px}.data-table{width:100%;font-size:.82rem}.data-table :deep(.el-table__header th){height:42px;background:#f8fafc;color:var(--text-secondary);font-weight:900}.table-main{display:block;color:var(--ink);font-weight:900;line-height:1.35}.table-sub{display:block;margin-top:3px;color:var(--text-muted);font-size:.72rem;line-height:1.35}.issue-tag{margin:2px 4px 2px 0}.muted{color:var(--text-muted)}.source-link{color:var(--primary);font-weight:800;text-decoration:none}.source-link:hover{text-decoration:underline}.pagination{justify-content:flex-end;margin-top:14px}.subject-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:14px}.subject-tile{min-height:88px;padding:14px;border:1px solid var(--line);border-radius:var(--radius-md);background:#f8fbff}.subject-tile strong,.subject-tile span{display:block}.subject-tile strong{color:var(--ink)}.subject-tile span{margin:6px 0 10px;color:var(--text-secondary);font-size:.78rem}.catalog-layout{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px}.catalog-layout h3{margin:0 0 10px;color:var(--ink);font-size:1rem}.compact{min-height:220px}.majors-table{margin-top:4px}@media(max-width:1180px){.stat-grid{grid-template-columns:repeat(3,1fr)}.subject-grid{grid-template-columns:repeat(2,1fr)}.catalog-layout{grid-template-columns:1fr}}@media(max-width:680px){.page-intro{flex-direction:column}.stat-grid,.subject-grid{grid-template-columns:1fr}.filter-input,.filter-select{width:100%}.toolbar{align-items:stretch}.toolbar .el-button{width:100%}}
</style>
