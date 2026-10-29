<template>
  <div class="target-page page-stack">
    <section class="page-intro"><div><span class="section-kicker">STEP 04</span><h2>目标分不是拍脑袋定的</h2><p>{{ store.selectedInstitution?.name }} · {{ store.selectedMajor?.name }} · {{ store.profile.examYear }} 年参考</p></div><el-button @click="router.push('/diagnosis')"><el-icon><Refresh /></el-icon>重做诊断</el-button></section>

    <el-alert v-if="!store.diagnosisComplete" title="尚未完成入学诊断，当前暂无有效基线分。请先完成诊断后再看分科目标与差距。" type="warning" show-icon :closable="false" />
    <section class="score-hero">
      <div class="target-number"><span>建议目标总分</span><strong>{{ store.targetScore ?? '—' }}</strong><small>{{ store.referenceScore == null ? '缺少可核实参考线，暂不生成目标分' : `参考线 ${store.referenceScore} + 安全分 30` }}</small></div>
      <div class="score-path"><div><span>诊断基线</span><b>{{ store.currentScore }}</b></div><i><span :style="{width:`${currentPercent}%`}"></span></i><div class="align-right"><span>目标分</span><b>{{ store.targetScore ?? '待核实' }}</b></div><p v-if="store.scoreGap != null">还需提升 <strong>{{ store.scoreGap }}</strong> 分；{{ store.targetDatePassed ? '目标达标日已到期：' : '距目标达标日：' }} <strong>{{ store.examDate }}</strong>{{ store.targetDatePassed ? '' : `，还有 ${store.daysUntilExam} 天` }}。该日期是规划节点，不是官方考试日。</p><p v-else>完成诊断后可查看薄弱项；参考线核实前不计算提分差距。</p></div>
      <div class="confidence" :class="{ verified: hasVerifiedScores }">
        <el-icon><component :is="hasVerifiedScores ? 'CircleCheck' : 'Warning'" /></el-icon>
        <p>
          <strong>当前可信度：{{ hasVerifiedScores ? '参考（基于官方公开线）' : '数据不足' }}</strong>
          <span v-if="hasVerifiedScores">参考线取自{{ sourceInfo.provider }} {{ sourceInfo.year }} 年{{ sourceInfo.line_type }}；不同省份线型不同，录取以当年招生简章为准。</span>
          <span v-else>该院校暂无可核实的公开参考线，目标分仅供初步参考。</span>
        </p>
      </div>
    </section>

    <el-alert v-if="store.targetDatePassed" type="warning" show-icon :closable="false"
      :title="`${store.profile.examYear} 年目标达标日已到期，请调整报考年度。`">
      <template #default><el-button text type="primary" @click="router.push('/profile')">调整报考年度</el-button></template>
    </el-alert>

    <section v-if="feas && !store.targetDatePassed" class="feasibility" :class="feas.feasible ? 'ok' : 'risk'">
      <span class="feas-icon"><el-icon><component :is="feas.feasible ? 'AlarmClock' : 'Warning'" /></el-icon></span>
      <div class="feas-main">
        <strong>{{ feas.feasible ? '按当前投入，时间预算可覆盖预计学时' : '时间预算偏紧，可调整学习投入' }}</strong>
        <p>
          距目标达标日约 <b>{{ feas.weeksLeft }}</b> 周 · 每周 <b>{{ feas.weeklyHours }}</b> 小时 ·
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
        <div v-if="hasVerifiedScores" class="history-chart"><div v-for="item in store.selectedInstitution.scores" :key="`${item.year}-${item.score}`" class="history-col"><strong>{{ item.score }}</strong><i :style="{height:`${Math.min(92, item.score/1.6)}%`}"></i><span>{{ item.year }}</span></div></div>
        <el-empty v-else description="暂无可核实的公开参考线" :image-size="64" />
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

    <el-card v-if="store.targetScore != null" shadow="never" class="analysis-card subjects-card">
      <template #header><div class="card-heading"><div><span class="section-kicker">提分分配</span><h3>各科建议目标</h3></div><span>{{ store.currentScore >= store.targetScore ? '诊断基线已达到基础目标，分科计划保留当前水平' : `基础目标 ${store.targetScore} 分 · 分科计划 ${allocatedTotal} 分（含 ${allocatedTotal - store.targetScore} 分波动余量）` }}</span></div></template>
      <div class="subject-targets"><div v-for="item in subjectTargets" :key="item.name" class="subject-cell"><div class="subject-cell-top"><strong>{{ item.name }}</strong><span>{{ item.current }} → <b>{{ item.target }}</b></span></div><el-progress :percentage="item.target ? Math.round(item.current/item.target*100) : 0" :show-text="false" :stroke-width="8" /><small>掌握度 {{ item.mastery }}% · 建议提升 {{ item.gap }} 分 · {{ item.strategy }}</small><div v-if="item.weakPoints.length" class="weak-chips"><span v-for="point in item.weakPoints" :key="point.id">{{ point.name }} · {{ point.mastery }}%</span></div></div></div>
    </el-card>

    <section class="method-card"><span class="method-icon"><el-icon><DataAnalysis /></el-icon></span><div><h3>目标分计算方式</h3><p v-if="store.targetScore != null">以可核实的公开参考线加 30 分作为基础目标；分科计划在此基础上增加约 5% 波动余量，再按诊断薄弱项分配。学时估算仅用于安排学习量，不能预测录取或保证达标。</p><p v-else>该院校缺少可核实参考线，暂不计算目标分和所需学时。仍可根据诊断薄弱项安排练习，报考要求请以当年官方公告为准。</p></div><el-button type="primary" size="large" @click="router.push(store.targetDatePassed ? '/profile' : '/plan')">{{ store.targetDatePassed ? '调整报考年度' : '查看学习路线' }}<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button></section>
  </div>
</template>

<script setup>
import { computed } from 'vue';import { useRouter } from 'vue-router';import { useApplicationStore } from '../stores/application'
const router=useRouter();const store=useApplicationStore();const currentPercent=computed(()=>store.targetScore ? Math.min(100,Math.round(store.currentScore/store.targetScore*100)) : 0)
const subjectTargets=computed(()=>store.subjectTargets)
const focusKnowledge=computed(()=>store.focusKnowledge)
const allocatedTotal=computed(()=>subjectTargets.value.reduce((sum,item)=>sum+item.target,0))
const sourceInfo=computed(()=>store.selectedInstitution?.source||{})
const hasVerifiedScores=computed(()=>store.referenceScore != null)
const feas=computed(()=>store.feasibility)
</script>

<style scoped lang="less" src="../styles/views/Target.less"></style>
