<template>
  <div class="schools-page page-stack">
    <section class="page-intro">
      <div><span class="section-kicker">STEP 02</span><h2>{{ store.selectedMajor?.category }}招生院校</h2><p>{{ provinceText }}<span v-if="cityText"> · {{ cityText }}</span> · {{ store.profile.examYear }} 年参考 · 目标专业：{{ store.selectedMajor?.name }}</p></div>
      <el-button @click="router.push('/profile')"><el-icon><Edit /></el-icon>修改专业</el-button>
    </section>

    <el-alert title="院校与分数线来自已接入省份公开数据：江苏为院校投档线，河南目前包含省控线与 2025 年征集志愿备档线；具体专业与录取结果以院校当年招生简章和考试院正式录取为准。" type="info" show-icon :closable="false" />

    <div class="subject-strip">
      <span><el-icon><Tickets /></el-icon>统考科目</span>
      <el-tag v-for="subject in store.selectedMajor?.subjects" :key="subject" effect="plain">{{ subject }}</el-tag>
      <small>专业类别决定统考科目，下列院校按该科类招生；院校如有加试会单独标注。</small>
    </div>

    <section class="school-layout">
      <div class="school-list">
        <article v-for="school in store.filteredInstitutions" :key="school.code" class="school-card" :class="{ selected: store.selectedInstitutionCode === school.code }" @click="store.selectInstitution(school.code)">
          <div class="school-head">
            <div class="school-avatar"><el-icon><School /></el-icon></div>
            <div class="school-name"><div><h3>{{ school.name }}</h3><el-tag v-if="store.selectedInstitutionCode === school.code" type="success" size="small">已选择</el-tag><el-tag :type="school.majorMatch === 'exact' ? 'success' : 'info'" size="small" effect="plain">{{ school.majorMatch === 'exact' ? '专业匹配' : '科类匹配' }}</el-tag></div><p>{{ provinceName(school.province) }} · {{ school.city }} · {{ store.selectedMajor?.category }}</p></div>
            <el-radio :model-value="store.selectedInstitutionCode" :value="school.code" aria-label="选择院校" />
          </div>
          <div class="school-stats">
            <span><small>近年参考线</small><strong>{{ latestScore(school) }} 分</strong></span>
            <span><small>学制</small><strong>{{ school.duration }}</strong></span>
            <span><small>学费参考</small><strong>{{ school.tuition ? `¥${school.tuition}/年` : '暂未获取' }}</strong></span>
          </div>
          <div class="school-meta"><span><el-icon><Location /></el-icon>{{ school.teachingSite }}</span><span><el-icon><Medal /></el-icon>{{ school.degree }}</span></div>
        </article>
        <el-empty v-if="store.filteredInstitutions.length === 0" :description="cityText ? `所选城市（${cityText}）暂无该科类招生院校，试试取消城市筛选或更换城市` : '所选省份暂无该类别的招生院校数据'" />
      </div>

      <aside class="compare-panel" v-if="selected">
        <span class="section-kicker">目标预览</span><h3>{{ selected.name }}</h3><p>{{ store.selectedMajor?.category }} · {{ selected.duration }}</p>
        <div class="score-history"><div v-for="score in selected.scores" :key="score.year"><span>{{ score.year }}</span><b>{{ score.score }}</b><i :style="{ width: barWidth(score.score) }"></i></div></div>
        <dl><div><dt>教学点</dt><dd>{{ selected.teachingSite }}</dd></div><div><dt>学位条件</dt><dd>{{ selected.degree }}</dd></div>
          <div v-if="matchedPlans.length"><dt>匹配专业计划</dt><dd>{{ matchedPlansText }}</dd></div>
          <div><dt>数据来源</dt><dd>
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
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useApplicationStore } from '../stores/application'
const router=useRouter();const store=useApplicationStore();const selected=computed(()=>store.selectedInstitution)
const provinceText=computed(()=>store.selectedProvinces.map(item=>item.label).join('、'))
const cityText=computed(()=>(store.profile.cities||[]).join('、'))
const provinceName=code=>store.provinceOptions.find(item=>item.value===code)?.label
const latestScore=school=>school.scores[school.scores.length-1]?.score
const maxScore=computed(()=>Math.max(120,...(selected.value?.scores||[]).map(s=>s.score||0)))
const barWidth=score=>`${Math.min(100,Math.round((score||0)/maxScore.value*100))}%`
const matchedPlans=computed(() => {
  if (!selected.value || selected.value.majorMatch !== 'exact') return []
  return (selected.value.plans || []).filter(plan => plan.major_name === store.selectedMajor?.name)
})
const matchedPlansText=computed(() => matchedPlans.value
  .map(plan => `${plan.major_name}${plan.plan_count != null ? ` ${plan.plan_count}人` : ''}`)
  .join('、'))
function sourceLabel(source) {
  const label = `${source.provider || ''} · ${source.year} 年${source.line_type || ''}`
  if (source.line_type === '征集志愿备档线') return `${label}（余缺计划参考）`
  if (source.line_type === '省控线') return `${label}（最低控制线参考）`
  return label
}
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}.page-intro{display:flex;align-items:flex-start;justify-content:space-between}.page-intro h2{color:var(--ink);font-size:1.7rem}.page-intro p{margin-top:5px;color:var(--text-secondary)}.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}.subject-strip{display:flex;align-items:center;gap:9px;padding:15px 18px;border:1px solid #dbe6f5;border-radius:16px;background:#f5f9ff}.subject-strip>span{display:flex;align-items:center;gap:6px;margin-right:5px;color:var(--ink);font-weight:800;font-size:.84rem}.subject-strip small{margin-left:auto;color:var(--text-muted);font-size:.72rem}.school-layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:18px;align-items:start}.school-list{display:flex;flex-direction:column;gap:13px}.school-card{padding:20px;border:1px solid var(--line);border-radius:18px;background:#fff;cursor:pointer;transition:.2s ease}.school-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-sm)}.school-card.selected{border-color:#75a2f5;box-shadow:0 0 0 3px rgba(37,99,235,.08)}.school-head{display:flex;align-items:center;gap:13px}.school-avatar{width:44px;height:44px;display:grid;place-items:center;flex:0 0 auto;border-radius:13px;color:var(--primary);background:var(--primary-soft)}.school-name{flex:1}.school-name>div{display:flex;align-items:center;gap:8px}.school-name h3{color:var(--ink);font-size:1rem}.school-name p{color:var(--text-muted);font-size:.75rem}.school-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:17px 0;padding:14px;border-radius:13px;background:#f7f9fc}.school-stats span:not(:last-child){border-right:1px solid var(--line)}.school-stats small,.school-stats strong{display:block}.school-stats small{color:var(--text-muted);font-size:.7rem}.school-stats strong{color:var(--ink);font-size:.9rem}.school-meta{display:flex;flex-wrap:wrap;gap:6px 18px;color:var(--text-secondary);font-size:.74rem}.school-meta span{display:flex;align-items:center;gap:6px}.compare-panel{position:sticky;top:98px;padding:22px;border-radius:20px;color:#dce8f9;background:linear-gradient(150deg,#15243f,#24446f);box-shadow:var(--shadow-md)}.compare-panel h3{color:#fff;font-size:1.2rem}.compare-panel>p{color:#aebfd8;font-size:.8rem}.score-history{display:flex;flex-direction:column;gap:12px;margin:22px 0}.score-history>div{display:grid;grid-template-columns:40px 34px 1fr;align-items:center;gap:8px;font-size:.74rem}.score-history b{color:#fff}.score-history i{display:block;height:5px;border-radius:6px;background:#64a2ff}.compare-panel dl{display:flex;flex-direction:column;gap:12px;padding-top:16px;border-top:1px solid rgba(255,255,255,.13)}.compare-panel dt{color:#8fa8cb;font-size:.68rem}.compare-panel dd{color:#ecf3ff;font-size:.76rem}.source-badge{margin-left:6px}.source-link{display:inline-block;margin-top:4px;color:#9fc3ff;font-size:.72rem;text-decoration:underline}.continue-button{width:100%;margin-top:20px}.compare-panel .section-kicker{color:#78a9f8}
@media(max-width:1000px){.school-layout{grid-template-columns:1fr}.compare-panel{position:static}}@media(max-width:650px){.page-intro{gap:12px}.subject-strip{flex-wrap:wrap}.subject-strip small{width:100%;margin:4px 0 0}.school-stats{grid-template-columns:1fr}.school-stats span:not(:last-child){padding-bottom:8px;border-right:0;border-bottom:1px solid var(--line)}}
</style>
