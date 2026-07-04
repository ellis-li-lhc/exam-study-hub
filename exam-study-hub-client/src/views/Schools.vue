<template>
  <div class="schools-page page-stack">
    <section class="page-intro">
      <div><span class="section-kicker">STEP 02</span><h2>{{ store.selectedMajor?.name }}相关招生院校</h2><p>招生省份：{{ provinceText }}<span v-if="cityText"> · 意向城市：{{ cityText }}</span> · {{ store.profile.examYear }} 年参考 · 科类：{{ store.selectedMajor?.category }}</p></div>
      <el-button @click="router.push('/profile')"><el-icon><Edit /></el-icon>修改专业</el-button>
    </section>

    <el-alert title="院校与分数线来自已接入省份公开数据：江苏包含院校投档线与 2025 年本科征求计划，河南目前包含省控线与 2025 年征集志愿备档线；具体专业与录取结果以院校当年招生简章和考试院正式录取为准。" type="info" show-icon :closable="false" />

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
        <el-empty v-if="store.filteredInstitutions.length === 0" :description="cityText ? `所选城市（${cityText}）暂无该科类招生院校，试试取消城市筛选或更换城市` : '所选省份暂无该类别的招生院校数据'" />
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
import { isCityInProvince } from '../data/regions'
import { institutionDataProfile, latestReferenceScore, matchedPlansForMajor } from '../data/institutionQuality'
const router=useRouter();const store=useApplicationStore();const selected=computed(()=>store.selectedInstitution)
const provinceText=computed(()=>store.selectedProvinces.map(item=>item.label).join('、'))
const cityText=computed(()=>(store.profile.cities||[]).join('、'))
const provinceName=code=>store.provinceOptions.find(item=>item.value===code)?.label
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

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}.page-intro{display:flex;align-items:flex-start;justify-content:space-between}.page-intro h2{color:var(--ink);font-size:1.55rem}.page-intro p{margin-top:5px;color:var(--text-secondary)}.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.7rem;font-weight:900;letter-spacing:.08em}.subject-strip{display:flex;align-items:center;gap:9px;padding:14px 16px;border:1px solid var(--line);border-radius:var(--radius-md);background:#fff}.subject-strip>span{display:flex;align-items:center;gap:6px;margin-right:5px;color:var(--ink);font-weight:900;font-size:.84rem}.subject-strip small{margin-left:auto;color:var(--text-muted);font-size:.72rem}.school-layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:16px;align-items:start}.school-list{display:flex;flex-direction:column;gap:12px}.school-card{padding:18px;border:1px solid var(--line);border-radius:var(--radius-lg);background:#fff;box-shadow:var(--shadow-xs);cursor:pointer;transition:.2s ease}.school-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-sm)}.school-card.selected{border-color:#9db7ea;box-shadow:0 0 0 3px rgba(29,78,216,.08)}.school-head{display:flex;align-items:center;gap:13px}.school-avatar{width:42px;height:42px;display:grid;place-items:center;flex:0 0 auto;border-radius:12px;color:var(--primary);background:var(--primary-soft)}.school-name{flex:1;min-width:0}.school-name>div{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.school-name h3{color:var(--ink);font-size:1rem}.school-name p{color:var(--text-muted);font-size:.75rem}.school-location{display:flex;flex-wrap:wrap;gap:3px 12px;margin-top:4px}.school-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0;padding:13px;border-radius:var(--radius-md);background:var(--surface-soft)}.school-stats span:not(:last-child){border-right:1px solid var(--line)}.school-stats small,.school-stats strong{display:block}.school-stats small{color:var(--text-muted);font-size:.7rem}.school-stats strong{color:var(--ink);font-size:.9rem}.school-meta{display:flex;flex-wrap:wrap;gap:6px 18px;color:var(--text-secondary);font-size:.74rem}.school-meta span{display:flex;align-items:center;gap:6px}.quality-row{display:flex;align-items:center;flex-wrap:wrap;gap:7px;margin-top:14px;padding-top:12px;border-top:1px solid var(--line)}.quality-score,.quality-check{display:inline-flex;align-items:center;min-height:24px;border-radius:999px;font-size:.68rem;font-weight:800}.quality-score{padding:0 10px;color:#5f6f89;background:#eef3fb}.quality-verified{color:#047857;background:#dff7ec}.quality-reference{color:#1d4ed8;background:#e7efff}.quality-partial,.quality-incomplete{color:#b45309;background:#fff2d8}.quality-check{padding:0 8px;color:#8b97a9;background:#f6f8fb}.quality-check.ok{color:#166534;background:#e8f7ed}.compare-panel{position:sticky;top:92px;padding:20px;border-radius:var(--radius-lg);color:#dce8f9;background:#111f33;box-shadow:var(--shadow-md)}.compare-panel h3{color:#fff;font-size:1.12rem}.compare-panel>p{color:#b8c7d9;font-size:.8rem;line-height:1.6}.score-history{display:flex;flex-direction:column;gap:12px;margin:20px 0}.score-history>div{display:grid;grid-template-columns:40px 34px 1fr;align-items:center;gap:8px;font-size:.74rem}.score-history b{color:#fff}.score-history i{display:block;height:5px;border-radius:6px;background:#79a7f5}.compare-panel dl{display:flex;flex-direction:column;gap:12px;padding-top:16px;border-top:1px solid rgba(255,255,255,.13)}.compare-panel dt{color:#9fb1c8;font-size:.68rem}.compare-panel dd{color:#ecf3ff;font-size:.76rem;line-height:1.55}.quality-detail{font-weight:900;color:#fff}.source-badge{margin-left:6px}.source-link{display:inline-block;margin-top:4px;color:#9fc3ff;font-size:.72rem;text-decoration:underline}.continue-button{width:100%;margin-top:20px}.compare-panel .section-kicker{color:#9fc3ff}.empty-panel{background:#17283f}.empty-panel .continue-button{color:#8fa4c0;background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.15)}
@media(max-width:1000px){.school-layout{grid-template-columns:1fr}.compare-panel{position:static}}@media(max-width:650px){.page-intro{gap:12px}.subject-strip{flex-wrap:wrap}.subject-strip small{width:100%;margin:4px 0 0}.school-stats{grid-template-columns:1fr}.school-stats span:not(:last-child){padding-bottom:8px;border-right:0;border-bottom:1px solid var(--line)}}
</style>
