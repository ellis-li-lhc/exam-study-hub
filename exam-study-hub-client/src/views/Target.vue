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
          <strong>当前可信度：{{ hasVerifiedScores ? '参考（基于官方公开线）' : '数据不足' }}</strong>
          <span v-if="hasVerifiedScores">参考线取自{{ sourceInfo.provider }} {{ sourceInfo.year }} 年{{ sourceInfo.line_type }}；不同省份线型不同，录取以当年招生简章为准。</span>
          <span v-else>该院校暂无可核实的公开参考线，目标分仅供初步参考。</span>
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
        <template #header><div class="card-heading"><div><span class="section-kicker">近年数据</span><h3>录取参考线</h3></div><el-tag size="small" type="info">院校 / 科类参考</el-tag></div></template>
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

    <section class="method-card"><span class="method-icon"><el-icon><DataAnalysis /></el-icon></span><div><h3>目标分计算方式</h3><p>成人高考通常不公布逐专业录取线，本系统按当前院校可核实公开线取有效参考值，再增加 30 分安全空间。分科目标结合诊断掌握度分配，优先把增量投到提分空间大、效率高的科目。招生人数变化会影响结果，因此这不是录取承诺。</p></div><el-button type="primary" size="large" @click="router.push('/plan')">生成学习路线<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button></section>
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

<style scoped lang="less" src="../styles/views/Target.less"></style>
