<template>
  <div class="schools-page page-stack">
    <section class="page-intro">
      <div><span class="section-kicker">STEP 02</span><h2>{{ store.selectedMajor?.name }}相关招生院校</h2><p>招生省份：{{ provinceText }}<span v-if="cityText"> · 院校所在地偏好：{{ cityText }}</span> · {{ store.profile.examYear }} 年参考 · 科类：{{ store.selectedMajor?.category }}</p></div>
      <el-button @click="router.push('/profile')"><el-icon><Edit /></el-icon>修改专业</el-button>
    </section>

    <el-alert title="河南/江苏/浙江公开数据试运行版：浙江已接入2025官方招生专业目录，但计划人数与院校线暂未公开；院校/专业/录取以当年考试院和院校招生简章为准，不构成录取承诺。" type="info" show-icon :closable="false" />

    <div class="subject-strip">
      <span><el-icon><Tickets /></el-icon>统考科目</span>
      <el-tag v-for="subject in store.selectedMajor?.subjects" :key="subject" effect="plain">{{ subject }}</el-tag>
      <small>{{ matchHint }}</small>
    </div>

    <section class="school-layout">
      <div class="school-list">
        <article v-for="school in store.filteredInstitutions" :key="school.code" class="school-card" :class="{ selected: store.selectedInstitutionCode === school.code }" @click="store.selectInstitution(school.code)">
          <div class="school-head">
            <div class="school-avatar"><el-icon><School /></el-icon></div>
            <div class="school-name"><div><h3>{{ school.name }}</h3><el-tag v-if="store.selectedInstitutionCode === school.code" type="success" size="small">已选择</el-tag><el-tag :type="school.majorMatch === 'exact' ? 'success' : 'info'" size="small" effect="plain">{{ matchModeLabel(school) }}</el-tag><el-tag v-if="!isLocalSchool(school)" type="warning" size="small" effect="plain">外省院校在{{ provinceName(school.province) }}招生</el-tag></div><p class="school-location"><span>招生省份：{{ provinceName(school.province) }}</span><span>院校所在地：{{ school.city }}</span><span>{{ store.selectedMajor?.category }}</span></p></div>
            <el-radio :model-value="store.selectedInstitutionCode" :value="school.code" aria-label="选择院校" />
          </div>
          <div class="school-stats">
            <span><small>近年参考线</small><strong>{{ scoreText(school) }}</strong></span>
            <span><small>学制</small><strong>{{ school.duration }}</strong></span>
            <span><small>学费参考</small><strong>{{ tuitionText(school) }}</strong></span>
          </div>
          <div class="school-meta"><span><el-icon><Location /></el-icon>{{ school.teachingSite }}</span><span><el-icon><Medal /></el-icon>{{ school.degree }}</span></div>
          <div class="quality-row">
            <span class="quality-score" :class="`quality-${qualityProfile(school).level}`">{{ qualityProfile(school).label }} · {{ qualityProfile(school).completed }}/{{ qualityProfile(school).total }}</span>
            <span v-for="check in qualityProfile(school).checks" :key="check.key" class="quality-check" :class="{ ok: check.ok }">{{ check.label }}</span>
          </div>
        </article>
        <el-empty v-if="store.filteredInstitutions.length === 0" :description="emptySchoolsText" />
      </div>

      <aside class="compare-panel" v-if="selected">
        <span class="section-kicker">目标预览</span><h3>{{ selected.name }}</h3><p>{{ store.selectedMajor?.category }} · {{ selected.duration }}</p>
        <div class="score-history"><div v-for="score in selected.scores" :key="score.year"><span>{{ score.year }}</span><b>{{ score.score }}</b><i :style="{ width: barWidth(score.score) }"></i></div></div>
        <dl><div><dt>教学点</dt><dd>{{ selected.teachingSite }}</dd></div><div><dt>学位条件</dt><dd>{{ selected.degree }}</dd></div>
          <div><dt>招生省份</dt><dd>{{ provinceName(selected.province) }}</dd></div>
          <div><dt>院校所在地</dt><dd>{{ selected.city }}<el-tag v-if="!isLocalSchool(selected)" size="small" type="warning" effect="dark" class="source-badge">外省院校</el-tag></dd></div>
          <div><dt>匹配口径</dt><dd>{{ matchDetail(selected) }}</dd></div>
          <div><dt>数据完整度</dt><dd><span class="quality-detail">{{ selectedProfile.label }} · {{ selectedProfile.completed }}/{{ selectedProfile.total }}</span><br>{{ selectedProfile.summary }}</dd></div>
          <div v-if="matchedPlans.length"><dt>匹配专业计划</dt><dd>{{ matchedPlansText }}</dd></div>
          <div><dt>参考线来源</dt><dd>
            <template v-if="selected.source && selected.source.confidence === 'verified'">
              {{ sourceLabel(selected.source) }}
              <el-tag size="small" type="success" effect="dark" class="source-badge">已核实</el-tag>
              <a v-if="selected.source.url" :href="selected.source.url" target="_blank" rel="noopener" class="source-link">查看原始文件</a>
            </template>
            <template v-else>{{ selected.sourceStatus }}</template>
          </dd></div>
        </dl>
        <el-button type="primary" size="large" class="continue-button" @click="router.push('/diagnosis')">确认目标并开始诊断<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button>
      </aside>
      <aside class="compare-panel empty-panel" v-else>
        <span class="section-kicker">目标预览</span>
        <h3>先选择一所院校</h3>
        <p>点击左侧院校后，再确认目标并开始诊断。</p>
        <dl><div><dt>当前结果</dt><dd>{{ store.filteredInstitutions.length }} 所可参考院校</dd></div><div><dt>匹配说明</dt><dd>{{ matchHint }}</dd></div></dl>
        <el-button size="large" class="continue-button" disabled>选择院校后继续</el-button>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useApplicationStore } from '../stores/application'
import { cityPreferenceLabel, isCityInProvince } from '../data/regions'
import { institutionDataProfile, latestReferenceScore, matchedPlansForMajor } from '../data/institutionQuality'
const router=useRouter();const store=useApplicationStore();const selected=computed(()=>store.selectedInstitution)
const provinceText=computed(()=>store.selectedProvinces.map(item=>item.label).join('、'))
const cityText=computed(()=>(store.profile.cities||[]).map(cityPreferenceLabel).join('、'))
const provinceName=code=>store.provinceOptions.find(item=>item.value===code)?.label
const emptySchoolsText=computed(()=>{
  if (store.institutionsError) return '院校数据加载失败，请刷新页面或稍后重试'
  if (!store.institutionsLoaded) return '正在加载院校数据…'
  if (!store.institutions.length) return '暂无院校数据，请确认后端服务与数据种子是否就绪'
  if (cityText.value) return `所选所在地偏好（${cityText.value}）暂无该科类招生院校，试试取消所在地筛选或勾选省外院校`
  return '所选省份暂无该类别的招生院校数据'
})
const maxScore=computed(()=>Math.max(120,...(selected.value?.scores||[]).map(s=>s.score||0)))
const barWidth=score=>`${Math.min(100,Math.round((score||0)/maxScore.value*100))}%`
const matchStats=computed(() => store.filteredInstitutions.reduce((stats, school) => {
  stats[school.majorMatch === 'exact' ? 'exact' : 'category'] += 1
  return stats
}, { exact: 0, category: 0 }))
const matchHint=computed(() => {
  const { exact, category } = matchStats.value
  if (exact && category) return `含 ${exact} 所公开专业计划匹配院校、${category} 所按科类参考线匹配院校。`
  if (exact) return `下列院校均来自公开专业计划，已匹配到 ${store.selectedMajor?.name}。`
  return `当前省份暂无完整公开专业计划，下列院校按 ${store.selectedMajor?.category} 科类参考线匹配。`
})
const isLocalSchool=school=>isCityInProvince(school.province, school.city)
const matchModeLabel=school=>school.majorMatch === 'exact' ? '专业计划匹配' : '科类参考匹配'
const matchDetail=school=>school.majorMatch === 'exact'
  ? `公开专业计划包含 ${store.selectedMajor?.name}`
  : `按 ${store.selectedMajor?.category} 科类参考线匹配，具体专业以当年招生计划为准`
const qualityProfile=school=>institutionDataProfile(school, store.selectedMajor)
const selectedProfile=computed(()=>selected.value ? qualityProfile(selected.value) : institutionDataProfile(null, store.selectedMajor))
const scoreText=school=>{
  const score = latestReferenceScore(school)?.score
  return Number.isFinite(Number(score)) ? `${score} 分` : '暂无参考线'
}
const tuitionText=school=>school.tuition !== null && school.tuition !== undefined && school.tuition !== '' && Number.isFinite(Number(school.tuition)) ? `¥${school.tuition}/年` : '暂未获取'
const matchedPlans=computed(() => {
  return matchedPlansForMajor(selected.value, store.selectedMajor?.name)
})
const matchedPlansText=computed(() => matchedPlans.value
  .map(plan => `${plan.major_name}${plan.plan_count != null ? ` ${plan.plan_count}人` : ''}`)
  .join('、'))
function sourceLabel(source) {
  const label = `${source.provider || ''} · ${source.year} 年${source.line_type || ''}`
  if (source.line_type === '征集志愿备档线') return `${label}（余缺计划参考）`
  if (source.line_type === '征求计划') return `${label}（余缺计划参考）`
  if (source.line_type === '省控线') return `${label}（最低控制线参考）`
  return label
}
</script>

<style scoped lang="less" src="../styles/views/Schools.less"></style>
