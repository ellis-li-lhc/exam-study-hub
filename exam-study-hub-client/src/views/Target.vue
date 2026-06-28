<template>
  <div class="target-page page-stack">
    <section class="page-intro"><div><span class="section-kicker">STEP 04</span><h2>目标分不是拍脑袋定的</h2><p>{{ store.selectedInstitution?.name }} · {{ store.selectedMajor?.name }} · {{ store.profile.examYear }} 年参考</p></div><el-button @click="router.push('/diagnosis')"><el-icon><Refresh /></el-icon>重做诊断</el-button></section>

    <el-alert v-if="!store.diagnosisComplete" title="尚未完成诊断，当前分数为示例初始值。建议先完成入学诊断。" type="warning" show-icon :closable="false" />
    <section class="score-hero">
      <div class="target-number"><span>建议目标总分</span><strong>{{ store.targetScore }}</strong><small>参考线 {{ store.referenceScore }} + 安全分 30</small></div>
      <div class="score-path"><div><span>当前预估</span><b>{{ store.currentScore }}</b></div><i><span :style="{width:`${currentPercent}%`}"></span></i><div class="align-right"><span>目标分</span><b>{{ store.targetScore }}</b></div><p>还需提升 <strong>{{ store.scoreGap }}</strong> 分，距目标考期 <strong>{{ store.examDate }}</strong> 还有 <strong>{{ store.daysUntilExam }}</strong> 天。</p></div>
      <div class="confidence" :class="{ verified: hasVerifiedScores }">
        <el-icon><component :is="hasVerifiedScores ? 'CircleCheck' : 'Warning'" /></el-icon>
        <p>
          <strong>当前可信度：{{ hasVerifiedScores ? '参考（基于官方投档线）' : '数据不足' }}</strong>
          <span v-if="hasVerifiedScores">参考线取自{{ sourceInfo.provider }} {{ sourceInfo.year }} 年{{ sourceInfo.line_type }}；成人高考不公布专业线，录取以当年招生简章为准。</span>
          <span v-else>该院校暂无可核实的投档线，目标分仅供初步参考。</span>
        </p>
      </div>
    </section>

    <section class="feasibility" :class="feas.feasible ? 'ok' : 'risk'">
      <span class="feas-icon"><el-icon><component :is="feas.feasible ? 'AlarmClock' : 'Warning'" /></el-icon></span>
      <div class="feas-main">
        <strong>{{ feas.feasible ? '时间充足，按当前投入可达标' : feas.weeksLeft <= 0 ? '目标考期已到，建议调整报考年度' : '时间偏紧，需加大投入或下调目标' }}</strong>
        <p>
          距目标考期约 <b>{{ feas.weeksLeft }}</b> 周 · 每周 <b>{{ feas.weeklyHours }}</b> 小时 ·
          可投入约 <b>{{ feas.availableHours }}</b> 小时,达标约需 <b>{{ feas.requiredHours }}</b> 小时。
          <template v-if="!feas.feasible && feas.weeksLeft > 0">
            仍缺约 <b class="warn">{{ feas.shortfallHours }}</b> 小时,建议每周再增加约 <b class="warn">{{ feas.extraWeekly }}</b> 小时,或适当下调目标分。
          </template>
        </p>
      </div>
    </section>

    <section class="analysis-grid">
      <el-card shadow="never" class="analysis-card reference-card">
        <template #header><div class="card-heading"><div><span class="section-kicker">近年数据</span><h3>录取参考线</h3></div><el-tag size="small" type="info">专业线优先</el-tag></div></template>
        <div class="history-chart"><div v-for="item in store.selectedInstitution?.scores" :key="item.year" class="history-col"><strong>{{ item.score }}</strong><i :style="{height:`${Math.min(92, item.score/1.6)}%`}"></i><span>{{ item.year }}</span></div></div>
      </el-card>

      <el-card shadow="never" class="analysis-card focus-card">
        <template #header><div class="card-heading"><div><span class="section-kicker">复习重点</span><h3>优先突破的知识模块</h3></div><el-tag size="small" type="warning" effect="light">掌握度低于 60% 优先</el-tag></div></template>
        <div v-if="focusKnowledge.length" class="focus-list">
          <article v-for="(point, index) in focusKnowledge" :key="point.id" class="focus-item">
            <span class="focus-rank">{{ index + 1 }}</span>
            <div class="focus-main">
              <div class="focus-top"><strong>{{ point.name }}</strong><el-tag size="small" effect="plain">{{ point.subject }}</el-tag></div>
              <el-progress :percentage="point.mastery" :stroke-width="6" :show-text="false" :color="point.mastery < 40 ? '#e6663d' : '#e6a23c'" />
            </div>
            <div class="focus-stat"><b>{{ point.mastery }}%</b><small>答对 {{ point.correct }}/{{ point.total }}</small></div>
          </article>
        </div>
        <el-empty v-else description="各知识点掌握度均达标，按学习路线巩固即可" :image-size="64" />
      </el-card>
    </section>

    <el-card shadow="never" class="analysis-card subjects-card">
      <template #header><div class="card-heading"><div><span class="section-kicker">提分分配</span><h3>各科建议目标</h3></div><span>合计 {{ allocatedTotal }} 分 · 结合诊断掌握度分配</span></div></template>
      <div class="subject-targets"><div v-for="item in subjectTargets" :key="item.name" class="subject-cell"><div class="subject-cell-top"><strong>{{ item.name }}</strong><span>{{ item.current }} → <b>{{ item.target }}</b></span></div><el-progress :percentage="item.target ? Math.round(item.current/item.target*100) : 0" :show-text="false" :stroke-width="8" /><small>掌握度 {{ item.mastery }}% · 建议提升 {{ item.gap }} 分 · {{ item.strategy }}</small><div v-if="item.weakPoints.length" class="weak-chips"><span v-for="point in item.weakPoints" :key="point.id">{{ point.name }} · {{ point.mastery }}%</span></div></div></div>
    </el-card>

    <section class="method-card"><span class="method-icon"><el-icon><DataAnalysis /></el-icon></span><div><h3>目标分计算方式</h3><p>成人高考公布到院校投档线（不单独公布专业录取线），取近三年较高有效值，再增加 30 分安全空间。分科目标结合诊断掌握度分配，优先把增量投到提分空间大、效率高的科目。招生人数变化会影响结果，因此这不是录取承诺。</p></div><el-button type="primary" size="large" @click="router.push('/plan')">生成学习路线<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button></section>
  </div>
</template>

<script setup>
import { computed } from 'vue';import { useRouter } from 'vue-router';import { useApplicationStore } from '../stores/application'
const router=useRouter();const store=useApplicationStore();const currentPercent=computed(()=>Math.min(100,Math.round(store.currentScore/store.targetScore*100)))
const subjectTargets=computed(()=>store.subjectTargets)
const focusKnowledge=computed(()=>store.focusKnowledge)
const allocatedTotal=computed(()=>subjectTargets.value.reduce((sum,item)=>sum+item.target,0))
const sourceInfo=computed(()=>store.selectedInstitution?.source||{})
const hasVerifiedScores=computed(()=>(store.selectedInstitution?.scores?.length||0)>0&&sourceInfo.value.confidence==='verified')
const feas=computed(()=>store.feasibility)
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}.page-intro{display:flex;align-items:flex-start;justify-content:space-between}.page-intro h2{color:var(--ink);font-size:1.7rem}.page-intro p{margin-top:5px;color:var(--text-secondary)}.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}.score-hero{display:grid;grid-template-columns:210px 1fr 260px;align-items:center;gap:28px;padding:30px;border-radius:22px;color:#dce8f9;background:linear-gradient(135deg,#14233e,#234875)}.target-number{padding-right:26px;border-right:1px solid rgba(255,255,255,.15)}.target-number span,.target-number small{display:block;color:#a9bedb;font-size:.73rem}.target-number strong{display:block;color:#fff;font-size:3.1rem;line-height:1.1}.score-path{display:grid;grid-template-columns:70px 1fr 70px;align-items:end;gap:10px}.score-path div span,.score-path div b{display:block}.score-path div span{color:#91a9ca;font-size:.67rem}.score-path div b{color:#fff;font-size:1.15rem}.score-path i{height:7px;margin-bottom:8px;border-radius:8px;background:rgba(255,255,255,.16);overflow:hidden}.score-path i span{display:block;height:100%;background:#66a3ff}.score-path .align-right{text-align:right}.score-path p{grid-column:1/-1;color:#b9c9df;font-size:.75rem}.score-path p strong{color:#fff}.confidence{display:flex;gap:10px;padding:14px;border-radius:14px;color:#ffd989;background:rgba(255,190,70,.1)}.confidence.verified{color:#9be7c2;background:rgba(70,200,150,.12)}
.feasibility{display:flex;align-items:flex-start;gap:13px;padding:16px 18px;border-radius:16px;border:1px solid var(--line)}.feasibility.ok{background:#f0faf4;border-color:#bfe8cf}.feasibility.risk{background:#fff7ea;border-color:#f6e0bd}.feas-icon{width:38px;height:38px;display:grid;place-items:center;flex:0 0 auto;border-radius:11px;font-size:19px}.feasibility.ok .feas-icon{color:#15a05a;background:#dcf3e5}.feasibility.risk .feas-icon{color:#c47d00;background:#fdedcf}.feas-main strong{display:block;color:var(--ink);font-size:.92rem}.feas-main p{margin-top:5px;color:var(--text-secondary);font-size:.78rem;line-height:1.6}.feas-main b{color:var(--ink)}.feas-main b.warn{color:#c0392b}.confidence p strong,.confidence p span{display:block}.confidence p strong{font-size:.76rem}.confidence p span{color:#d8c59d;font-size:.68rem;margin-top:3px}.analysis-grid{display:grid;grid-template-columns:0.72fr 1.28fr;gap:18px;align-items:stretch}.analysis-card{border-radius:20px;border-color:var(--line)}.subjects-card{margin-top:18px}:deep(.reference-card){display:flex;flex-direction:column}:deep(.reference-card .el-card__body){flex:1;display:flex;flex-direction:column}.card-heading{display:flex;align-items:center;justify-content:space-between}.card-heading h3{color:var(--ink)}.card-heading>span{color:var(--text-muted);font-size:.74rem}.history-chart{flex:1;display:flex;align-items:flex-end;justify-content:space-around;gap:18px;min-height:180px;padding-top:6px}.history-col{display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:7px;height:100%}.history-col strong{color:var(--ink);font-size:.86rem}.history-col i{width:30px;flex:0 0 auto;min-height:6px;border-radius:8px 8px 0 0;background:linear-gradient(180deg,#9cc0ff,#3976ef)}.history-col span{color:var(--text-secondary);font-size:.74rem}.subject-targets{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.subject-cell{padding:15px;border:1px solid var(--line);border-radius:14px;background:#fbfcfe}.subject-cell-top{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:9px}.subject-targets strong{color:var(--ink);font-size:.82rem}.subject-targets span{color:var(--text-muted);font-size:.75rem}.subject-targets span b{color:var(--primary)}.subject-targets small{display:block;margin-top:7px;color:var(--text-muted);font-size:.68rem}.weak-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}.weak-chips span{padding:3px 9px;border-radius:999px;color:#b45309;font-size:.66rem;background:#fdf3e3;border:1px solid #f6e0bd}.focus-list{display:grid;grid-template-columns:1fr 1fr;gap:10px}.focus-item{display:flex;align-items:center;gap:12px;padding:13px 15px;border:1px solid var(--line);border-radius:14px;background:#fbfcfe}.focus-rank{width:26px;height:26px;display:grid;place-items:center;flex:0 0 auto;border-radius:8px;color:#b45309;font-size:.72rem;font-weight:900;background:#fdf3e3}.focus-main{flex:1;min-width:0}.focus-top{display:flex;align-items:center;gap:8px;margin-bottom:7px;min-width:0}.focus-top strong{flex:1;min-width:0;color:var(--ink);font-size:.82rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.focus-top :deep(.el-tag){flex:0 0 auto}.focus-stat{text-align:right;flex:0 0 auto}.focus-stat b{display:block;color:var(--accent,#e6a23c);font-size:1rem}.focus-stat small{color:var(--text-muted);font-size:.64rem}.method-card{display:flex;align-items:center;gap:16px;padding:22px;border:1px solid var(--line);border-radius:18px;background:#fff}.method-icon{width:48px;height:48px;display:grid;place-items:center;flex:0 0 auto;border-radius:15px;color:var(--primary);background:var(--primary-soft)}.method-card>div{flex:1}.method-card h3{color:var(--ink);font-size:.95rem}.method-card p{color:var(--text-secondary);font-size:.76rem}
@media(max-width:1050px){.score-hero{grid-template-columns:180px 1fr}.confidence{grid-column:1/-1}.analysis-grid{grid-template-columns:1fr}.focus-list{grid-template-columns:1fr}.subject-targets{grid-template-columns:1fr}}@media(max-width:650px){.score-hero{grid-template-columns:1fr}.target-number{border-right:0;border-bottom:1px solid rgba(255,255,255,.15);padding:0 0 18px}.method-card{align-items:flex-start;flex-wrap:wrap}.method-card .el-button{width:100%}}
</style>

