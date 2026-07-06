<template>
  <div class="progress-page page-stack">
    <section class="page-intro"><div><span class="section-kicker">学习复盘</span><h2>看执行，也看阶段测试是否达标</h2><p>任务完成度、阶段测试和复习队列共同反映当前节奏。</p></div><el-button type="primary" plain @click="router.push('/plan')">回到学习路线</el-button></section>
    <section class="progress-hero"><div><span>总体任务进度</span><strong>{{ store.overallProgress }}%</strong><p>当前处于第 {{ store.currentStage }} 阶段：{{ currentStage?.name }}</p></div><el-progress :percentage="store.overallProgress" :stroke-width="14" :show-text="false"/><dl><div><dt>已完成任务</dt><dd>{{ completedTasks }}/{{ store.tasks.length }}</dd></div><div><dt>诊断基线分</dt><dd>{{ store.currentScore }}</dd></div><div><dt>目标分</dt><dd>{{ store.targetScore }}</dd></div><div><dt>距考试</dt><dd>{{ store.daysUntilExam }} 天</dd></div></dl></section>
    <section class="progress-grid">
      <el-card shadow="never" class="progress-card"><template #header><div class="card-heading"><h3>分科基础</h3><span>诊断基线</span></div></template><div class="subject-bars"><div v-for="subject in subjects" :key="subject"><div><strong>{{ subject }}</strong><span>{{ store.diagnostic.subjectScores[subject] || 0 }} / 150</span></div><el-progress :percentage="Math.round((store.diagnostic.subjectScores[subject]||0)/150*100)" :stroke-width="9" :show-text="false"/></div></div></el-card>
      <el-card shadow="never" class="progress-card"><template #header><div class="card-heading"><h3>阶段测试记录</h3><span>{{ store.stageTests.length }} 次</span></div></template><div v-if="store.stageTests.length" class="test-list"><div v-for="test in store.stageTests" :key="`${test.stage}-${test.date}`"><span>阶段 {{ test.stage }}</span><strong>{{ test.accuracy ?? Math.round(test.score / 450 * 100) }}% 正确率</strong><el-tag :type="test.passed?'success':'warning'" size="small">{{ test.passed?'达标':'建议复习' }}</el-tag><small>{{ test.date }}</small></div></div><el-empty v-else description="完成阶段测试后，这里会形成成绩轨迹" :image-size="72"/></el-card>
    </section>
  </div>
</template>
<script setup>
import { computed } from 'vue';import { useRouter } from 'vue-router';import { useApplicationStore } from '../stores/application';const router=useRouter();const store=useApplicationStore();const completedTasks=computed(()=>store.tasks.filter(item=>item.done).length);const currentStage=computed(()=>store.stages.find(item=>item.id===store.currentStage));const subjects=computed(()=>store.selectedMajor?.subjects||[])
</script>
<style scoped lang="less" src="../styles/views/Progress.less"></style>
