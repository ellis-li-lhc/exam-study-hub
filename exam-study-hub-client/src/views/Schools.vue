<template>
  <div class="schools-page page-stack">
    <section class="page-intro">
      <div><span class="section-kicker">STEP 02</span><h2>{{ store.selectedMajor?.name }}相关招生院校</h2><p>招生省份：{{ provinceText }}<span v-if="cityText"> · 院校所在地偏好：{{ cityText }}</span> · {{ store.profile.examYear }} 年参考 · 科类：{{ store.selectedMajor?.category }}</p></div>
      <el-button @click="router.push('/profile')"><el-icon><Edit /></el-icon>修改专业</el-button>
    </section>

    <el-alert :title="dataNotice" type="info" show-icon :closable="false" />

    <el-card v-if="categoryCollections.length" shadow="never">
      <details>
        <summary>历年院校科类征集计划 · {{ categoryCollections.length }} 条（点击展开）</summary>
        <p class="supplement-note">这是历史征集余缺人数，只到院校与科类，不代表当前招生人数，也不能分摊为具体专业计划。仅有征集记录的院校不作为专业报考目标。</p>
        <ul class="supplement-list"><li v-for="row in categoryCollections" :key="`${row.province}-${row.school}-${row.year}-${row.round}-${row.study_form}-${row.category_name}`">
          {{ provinceName(row.province) }} · {{ row.year }} 年 · {{ row.round }} · {{ row.school }} · {{ row.category_name }} · {{ row.study_form }} · {{ row.plan_count }} 人
          <a :href="row.source_url" target="_blank" rel="noopener" class="source-link">查看官方征集公告</a>
        </li></ul>
      </details>
    </el-card>

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
        <div class="score-history"><div v-for="score in selectedReferenceScores" :key="`${score.year}-${score.category_code || score.category_name}`"><span>{{ score.year }}</span><b>{{ score.score }}</b><i :style="{ width: barWidth(score.score) }"></i></div></div>
        <dl><div><dt>教学点</dt><dd>{{ selected.teachingSite }}</dd></div><div><dt>学位条件</dt><dd>{{ selected.degree }}</dd></div>
          <div><dt>招生省份</dt><dd>{{ provinceName(selected.province) }}</dd></div>
          <div><dt>院校所在地</dt><dd>{{ selected.city }}<el-tag v-if="!isLocalSchool(selected)" size="small" type="warning" effect="dark" class="source-badge">外省院校</el-tag></dd></div>
          <div><dt>匹配口径</dt><dd>{{ matchDetail(selected) }}</dd></div>
          <div><dt>数据完整度</dt><dd><span class="quality-detail">{{ selectedProfile.label }} · {{ selectedProfile.completed }}/{{ selectedProfile.total }}</span><br>{{ selectedProfile.summary }}</dd></div>
          <div v-if="matchedPlans.length"><dt>匹配专业计划</dt><dd>{{ matchedPlansText }}</dd></div>
          <div v-if="selectedControlScores.length"><dt>{{ provinceName(selected.province) }}最低控制线（非院校录取线）</dt><dd>
            <ul class="supplement-list"><li v-for="line in selectedControlScores" :key="`${line.year}-${line.category_name}-${line.round}`">
              {{ line.year }} 年 · {{ line.category_name }}<span v-if="selected.province === 'hebei'"> · 统考生</span> · {{ line.score }} 分
              <a :href="line.source_url" target="_blank" rel="noopener" class="source-link">查看来源公告</a>
            </li></ul>
            <p class="supplement-note">这是全省市该科类最低控制线，不能据此判断院校录取或生成院校提分目标；2026年控制线暂未收录。</p>
          </dd></div>
          <div v-if="selectedSpecialControlScores.length"><dt>农民工考生专项控制线</dt><dd>
            <ul class="supplement-list"><li v-for="line in selectedSpecialControlScores" :key="`${line.year}-${line.category_name}-${line.round}`">
              {{ line.year }} 年 · {{ line.category_name }} · {{ line.score }} 分
              <a :href="line.source_url" target="_blank" rel="noopener" class="source-link">查看来源公告</a>
            </li></ul>
            <p class="supplement-note">仅适用于相应专项资格及计划，不能作为普通统考生参考线。2023年专项线暂未收录。</p>
          </dd></div>
          <div v-if="detailedPlans.length"><dt>专业详情与报考条件</dt><dd>
            <p class="supplement-note">每条记录仅适用于标注年份和批次；未公布的人数、学费及教学点保留为未知。直属、委托培养和职业本科须核对招生对象与条件。</p>
            <ul class="supplement-list"><li v-for="plan in detailedPlans" :key="`${plan.year}-${plan.major_code}-${plan.round}`">
              <span>{{ plan.year }} 年 · {{ plan.round }} · 专业代码 {{ ['hubei', 'hunan', 'jiangxi', 'anhui', 'fujian', 'sichuan', 'chongqing', 'beijing', 'guangxi'].includes(selected.province) ? (plan.major_code_raw || '未公布') : plan.major_code }}</span><br>
              <p v-if="plan.institution_code_raw">当年院校编号 {{ plan.institution_code_raw }}<span v-if="plan.applicant_group"> · {{ plan.applicant_group }}</span></p>
              <strong>{{ plan.teaching_site || '教学点暂未获取' }}</strong><br>
              {{ tuitionForPlanText(plan) }} · {{ plan.plan_count == null ? '计划人数未公布' : `${plan.plan_count} 人` }}
              <p v-if="plan.study_duration_raw || plan.minimum_study_duration_raw"><span v-if="plan.study_duration_raw">学制 {{ plan.study_duration_raw }}</span><span v-if="plan.minimum_study_duration_raw">{{ plan.study_duration_raw ? ' · ' : '' }}最低学习年限 {{ plan.minimum_study_duration_raw }}</span></p>
              <p v-if="plan.major_direction">专业方向 {{ plan.major_direction }}</p>
              <p v-if="plan.study_form || plan.enrollment_scope">{{ [plan.study_form, plan.enrollment_scope].filter(Boolean).join(' · ') }}</p>
              <p v-if="plan.foreign_language">外语语种 {{ plan.foreign_language }}</p>
              <p v-if="plan.remarks">{{ plan.remarks }}</p>
              <a v-if="plan.source_url" :href="plan.source_page ? `${plan.source_url}#page=${plan.source_page}` : plan.source_url" target="_blank" rel="noopener" class="source-link">查看官方计划</a>
            </li></ul>
          </dd></div>
          <div v-if="verifiedFacts.length"><dt>已核验院校说明</dt><dd>
            <details v-for="fact in verifiedFacts" :key="`${fact.year}-${fact.source_id}-${fact.field}`" class="supplement-detail">
              <summary>{{ fact.year }} 年 · {{ factLabels[fact.field] || '院校说明' }}</summary>
              <p>{{ fact.source_excerpt }}</p>
              <a :href="fact.source_url" target="_blank" rel="noopener" class="source-link">查看院校原文</a>
            </details>
          </dd></div>
          <div v-if="supplementDocuments.length"><dt>院校补充资料</dt><dd>
            <details class="supplement-detail"><summary>{{ supplementDocuments.length }} 份官方资料（内容待逐项核验）</summary>
              <ul class="supplement-list"><li v-for="doc in supplementDocuments" :key="doc.source_id">
                <a :href="doc.source_url" target="_blank" rel="noopener">{{ doc.title }}</a>
                <small>{{ doc.review_status === 'ocr_requires_review' ? '图片识别内容待核验' : '已收录来源，字段待核验' }}</small>
              </li></ul>
            </details>
          </dd></div>
          <div><dt>招生数据来源</dt><dd>
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
import { controlScoresForMajor, institutionDataProfile, latestReferenceScore, matchedPlansForMajor, referenceScoresForMajor, tuitionForMajorText, tuitionForPlanText, verifiedFactsForMajor } from '../data/institutionQuality'
const router=useRouter();const store=useApplicationStore();const selected=computed(()=>store.selectedInstitution)
const provinceText=computed(()=>store.selectedProvinces.map(item=>item.label).join('、'))
const cityText=computed(()=>(store.profile.cities||[]).map(cityPreferenceLabel).join('、'))
const provinceName=code=>store.provinceOptions.find(item=>item.value===code)?.label
const categoryCollections=computed(()=>store.institutions
  .filter(s=>store.profile.provinces.includes(s.province))
  .flatMap(s=>(s.categoryCollectionPlans || []).map(row=>({...row,province:s.province,school:row.institution_name || s.name}))))
const coverageNotes={
  anhui:'安徽已抓取2026公开查询全部37页专升本目录，71所院校1104条专业/教学点记录（485个院校专业组合）；2024—2025省控线单列。21条专项限制记录不作为普通备考目标，招生人数未公布。',
  fujian:'福建已抓取2026公开查询全部25页，并筛出40所院校468条专升本记录（242个院校专业组合）；2025省控线单列。10条定向或委培等限制记录不作为普通备考目标，招生人数未公布；学费原文未注明计费周期的，不能当作年学费。',
  sichuan:'四川当前采用2026年11月5日第二次公布的49校1240条专升本计划，合计49031人；10条限定招生记录不作为普通目标。8月1329条目录保留历史，不参与当前匹配；2024—2025省控线单列，人数并非2027招生安排。',
  chongqing:'重庆已抓取2026官方公开查询36所院校472条专升本记录（250个院校专业组合）；2024—2025省控线单列。12条单位或委培等限制记录不作为普通备考目标；外语为英语，人数未作为公开计划导入，收费周期以原文为准。',
  beijing:'北京已抓取2026考试院公开专升本目录全部45所院校287条专业及教学点记录（197个院校专业及方向组合）；2024—2025市控线单列。10条限定招生记录不作为普通备考目标，目录未公布人数及学费，外语为英语。',
  guangxi:'广西已抓取2026考试院完整公开目录988条各层次记录，仅导入55所院校569条专升本记录（561个院校专业组合）；2024—2025省控线单列。9条单位限制记录不作为普通备考目标；未公开人数，收费按原文区分年费、学期费及总学费。',
  hunan:'湖南已接入2026省级目录56所院校677条专升本专业，学费、学制、人数和专业教学点未公布；2024—2025省控线及2025两轮科类征集分别展示。另5校仅有历史征集资料。',
  jiangxi:'江西接入14所院校2026年官方资料297条专业/教学点记录（255个院校专业组合），含3条科类待核实或科目冲突记录，已排除出备考目标，非全省完整目录；2025普通统考省控线独立展示，不含“一村一名大学生”专项，未公布字段保持未知。',
  hubei:'湖北当前接入5所院校2026年简章85条专业，非全省完整目录；2023—2025省控线和2024—2025院校科类征集计划分别展示。',
  hebei:'河北目前收录2024—2025年专升本计划，仅作历史参考；尚未取得2026完整目录和本科征集明细。统考生与农民工考生控制线分开标注。',
  shandong:'山东已接入2026及2025专升本目录、2025两次征集计划、2023—2025省控线。2026目录未公布计划人数、学费和教学点。'
}
const dataNotice=computed(()=>{
  const notes=store.profile.provinces.map(code=>coverageNotes[code]).filter(Boolean)
  return notes.length ? notes.join(' ')+'以上省份暂无院校实际录取线，报考以当年官方公告为准。'
    : '已接入河南、江苏、浙江、广东、上海、山东、河北、湖北、湖南、江西、安徽、福建、四川、重庆、北京、广西公开招生资料。省市控线、院校线及征集计划分开标注，资料仅适用于对应年份和批次，以当年官方公告为准。'
})
const emptySchoolsText=computed(()=>{
  if (store.institutionsError) return '院校数据加载失败，请刷新页面或稍后重试'
  if (!store.institutionsLoaded) return '正在加载院校数据…'
  if (!store.institutions.length) return '暂无院校数据，请确认后端服务与数据种子是否就绪'
  if (cityText.value) return `所选所在地偏好（${cityText.value}）暂无该科类招生院校，试试取消所在地筛选或勾选省外院校`
  return '所选省份暂无该类别的招生院校数据'
})
const selectedReferenceScores=computed(()=>referenceScoresForMajor(selected.value, store.selectedMajor?.name))
const selectedControlScores=computed(()=>controlScoresForMajor(selected.value, store.selectedMajor?.name))
const selectedSpecialControlScores=computed(()=>selected.value?.province === 'hebei'
  ? controlScoresForMajor(selected.value, store.selectedMajor?.name, { applicantGroup: '农民工考生' }) : [])
const maxScore=computed(()=>Math.max(120,...selectedReferenceScores.value.map(s=>s.score||0)))
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
const matchModeLabel=school=>school.province === 'hebei' ? `${school.activeCatalogYear}年计划参考` : school.majorMatch === 'exact' ? '专业计划匹配' : '科类参考匹配'
const matchDetail=school=>school.majorMatch === 'exact'
  ? `公开专业计划包含 ${store.selectedMajor?.name}`
  : `按 ${store.selectedMajor?.category} 科类参考线匹配，具体专业以当年招生计划为准`
const qualityProfile=school=>institutionDataProfile(school, store.selectedMajor)
const selectedProfile=computed(()=>selected.value ? qualityProfile(selected.value) : institutionDataProfile(null, store.selectedMajor))
const scoreText=school=>{
  const score = latestReferenceScore(school, store.selectedMajor?.name)?.score
  return score != null && Number.isFinite(Number(score)) ? `${score} 分` : '暂无参考线'
}
const tuitionText=school=>tuitionForMajorText(school, store.selectedMajor?.name)
const matchedPlans=computed(() => {
  return matchedPlansForMajor(selected.value, store.selectedMajor?.name)
})
const detailedPlans=computed(()=>matchedPlans.value.filter(plan=>plan.teaching_site || plan.tuition_raw || plan.study_duration_raw || plan.enrollment_scope || plan.remarks)
  .slice().sort((a,b)=>b.year-a.year || String(a.round).localeCompare(String(b.round), 'zh')))
const verifiedFacts=computed(()=>verifiedFactsForMajor(selected.value, store.selectedMajor?.name))
const supplementDocuments=computed(()=>selected.value?.supplementalData?.documents || [])
const factLabels={ duration_years:'学制', study_years_range:'修业年限', duration_by_major:'分专业学制', tuition_rules:'收费说明' }
const matchedPlansText=computed(() => matchedPlans.value
  .map(plan => `${plan.year}年${plan.round || ''} · ${plan.major_name}${plan.plan_count != null ? ` ${plan.plan_count}人` : ''}`)
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
