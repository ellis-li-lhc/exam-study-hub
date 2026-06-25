<template>
  <div class="target-page page-stack">
    <section class="page-intro"><div><span class="section-kicker">STEP 04</span><h2>目标分不是拍脑袋定的</h2><p>{{ store.selectedInstitution?.name }} · {{ store.selectedMajor?.name }} · {{ store.profile.examYear }} 年参考</p></div><el-button @click="router.push('/diagnosis')"><el-icon><Refresh /></el-icon>重做诊断</el-button></section>

    <el-alert v-if="!store.diagnosisComplete" title="尚未完成诊断，当前分数使用演示初始值。建议先完成入学诊断。" type="warning" show-icon :closable="false" />
    <section class="score-hero">
      <div class="target-number"><span>建议目标总分</span><strong>{{ store.targetScore }}</strong><small>参考线 {{ store.referenceScore }} + 安全分 30</small></div>
      <div class="score-path"><div><span>当前预估</span><b>{{ store.currentScore }}</b></div><i><span :style="{width:`${currentPercent}%`}"></span></i><div class="align-right"><span>目标分</span><b>{{ store.targetScore }}</b></div><p>还需提升 <strong>{{ store.scoreGap }}</strong> 分，按当前时间投入预计约 <strong>{{ store.estimatedWeeks }}</strong> 周。</p></div>
      <div class="confidence"><el-icon><Warning /></el-icon><p><strong>当前可信度：参考</strong><span>使用的是演示录取线，接入官方专业线后重新计算。</span></p></div>
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

    <section class="method-card"><span class="method-icon"><el-icon><DataAnalysis /></el-icon></span><div><h3>目标分计算方式</h3><p>优先使用专业录取线，其次院校线，最后才使用省控线；取近三年较高有效值，再增加 30 分安全空间。分科目标结合诊断掌握度分配，优先把增量投到提分空间大、效率高的科目。招生人数变化会影响结果，因此这不是录取承诺。</p></div><el-button type="primary" size="large" @click="router.push('/plan')">生成学习路线<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button></section>
  </div>
</template>

<script setup>
import { computed } from 'vue';import { useRouter } from 'vue-router';import { useApplicationStore } from '../stores/application'
const router=useRouter();const store=useApplicationStore();const currentPercent=computed(()=>Math.min(100,Math.round(store.currentScore/store.targetScore*100)))
const subjectTargets=computed(()=>store.subjectTargets)
const focusKnowledge=computed(()=>store.focusKnowledge)
const allocatedTotal=computed(()=>subjectTargets.value.reduce((sum,item)=>sum+item.target,0))
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}.page-intro{display:flex;align-items:flex-start;justify-content:space-between}.page-intro h2{color:var(--ink);font-size:1.7rem}.page-intro p{margin-top:5px;color:var(--text-secondary)}.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}.score-hero{display:grid;grid-template-columns:210px 1fr 260px;align-items:center;gap:28px;padding:30px;border-radius:22px;color:#dce8f9;background:linear-gradient(135deg,#14233e,#234875)}.target-number{padding-right:26px;border-right:1px solid rgba(255,255,255,.15)}.target-number span,.target-number small{display:block;color:#a9bedb;font-size:.73rem}.target-number strong{display:block;color:#fff;font-size:3.1rem;line-height:1.1}.score-path{display:grid;grid-template-columns:70px 1fr 70px;align-items:end;gap:10px}.score-path div span,.score-path div b{display:block}.score-path div span{color:#91a9ca;font-size:.67rem}.score-path div b{color:#fff;font-size:1.15rem}.score-path i{height:7px;margin-bottom:8px;border-radius:8px;background:rgba(255,255,255,.16);overflow:hidden}.score-path i span{display:block;height:100%;background:#66a3ff}.score-path .align-right{text-align:right}.score-path p{grid-column:1/-1;color:#b9c9df;font-size:.75rem}.score-path p strong{color:#fff}.confidence{display:flex;gap:10px;padding:14px;border-radius:14px;color:#ffd989;background:rgba(255,190,70,.1)}.confidence p strong,.confidence p span{display:block}.confidence p strong{font-size:.76rem}.confidence p span{color:#d8c59d;font-size:.68rem;margin-top:3px}.analysis-grid{display:grid;grid-template-columns:0.72fr 1.28fr;gap:18px;align-items:stretch}.analysis-card{border-radius:20px;border-color:var(--line)}.subjects-card{margin-top:18px}:deep(.reference-card){display:flex;flex-direction:column}:deep(.reference-card .el-card__body){flex:1;display:flex;flex-direction:column}.card-heading{display:flex;align-items:center;justify-content:space-between}.card-heading h3{color:var(--ink)}.card-heading>span{color:var(--text-muted);font-size:.74rem}.history-chart{flex:1;display:flex;align-items:flex-end;justify-content:space-around;gap:18px;min-height:180px;padding-top:6px}.history-col{display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:7px;height:100%}.history-col strong{color:var(--ink);font-size:.86rem}.history-col i{width:30px;flex:0 0 auto;min-height:6px;border-radius:8px 8px 0 0;background:linear-gradient(180deg,#9cc0ff,#3976ef)}.history-col span{color:var(--text-secondary);font-size:.74rem}.subject-targets{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.subject-cell{padding:15px;border:1px solid var(--line);border-radius:14px;background:#fbfcfe}.subject-cell-top{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:9px}.subject-targets strong{color:var(--ink);font-size:.82rem}.subject-targets span{color:var(--text-muted);font-size:.75rem}.subject-targets span b{color:var(--primary)}.subject-targets small{display:block;margin-top:7px;color:var(--text-muted);font-size:.68rem}.weak-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}.weak-chips span{padding:3px 9px;border-radius:999px;color:#b45309;font-size:.66rem;background:#fdf3e3;border:1px solid #f6e0bd}.focus-list{display:grid;grid-template-columns:1fr 1fr;gap:10px}.focus-item{display:flex;align-items:center;gap:12px;padding:13px 15px;border:1px solid var(--line);border-radius:14px;background:#fbfcfe}.focus-rank{width:26px;height:26px;display:grid;place-items:center;flex:0 0 auto;border-radius:8px;color:#b45309;font-size:.72rem;font-weight:900;background:#fdf3e3}.focus-main{flex:1;min-width:0}.focus-top{display:flex;align-items:center;gap:8px;margin-bottom:7px;min-width:0}.focus-top strong{flex:1;min-width:0;color:var(--ink);font-size:.82rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.focus-top :deep(.el-tag){flex:0 0 auto}.focus-stat{text-align:right;flex:0 0 auto}.focus-stat b{display:block;color:var(--accent,#e6a23c);font-size:1rem}.focus-stat small{color:var(--text-muted);font-size:.64rem}.method-card{display:flex;align-items:center;gap:16px;padding:22px;border:1px solid var(--line);border-radius:18px;background:#fff}.method-icon{width:48px;height:48px;display:grid;place-items:center;flex:0 0 auto;border-radius:15px;color:var(--primary);background:var(--primary-soft)}.method-card>div{flex:1}.method-card h3{color:var(--ink);font-size:.95rem}.method-card p{color:var(--text-secondary);font-size:.76rem}
@media(max-width:1050px){.score-hero{grid-template-columns:180px 1fr}.confidence{grid-column:1/-1}.analysis-grid{grid-template-columns:1fr}.focus-list{grid-template-columns:1fr}.subject-targets{grid-template-columns:1fr}}@media(max-width:650px){.score-hero{grid-template-columns:1fr}.target-number{border-right:0;border-bottom:1px solid rgba(255,255,255,.15);padding:0 0 18px}.method-card{align-items:flex-start;flex-wrap:wrap}.method-card .el-button{width:100%}}
</style>

