<template>
  <div class="progress-page page-stack">
    <section class="page-intro">
      <div>
        <span class="section-kicker">学习复盘</span>
        <h2>看执行，也看阶段测试是否达标</h2>
        <p>任务完成度、阶段轨迹、复习队列与测试记录共同反映当前节奏。</p>
      </div>
      <el-button type="primary" plain @click="router.push('/plan')">回到学习路线</el-button>
    </section>

    <section class="progress-hero">
      <div>
        <span>今日任务完成度</span>
        <strong>{{ store.overallProgress }}%</strong>
        <p>当前处于第 {{ store.currentStage }} 阶段：{{ currentStage?.name || '—' }}</p>
      </div>
      <el-progress :percentage="store.overallProgress" :stroke-width="14" :show-text="false" />
      <dl>
        <div><dt>今日任务</dt><dd>{{ completedTasks }}/{{ store.tasks.length }}</dd></div>
        <div><dt>诊断基线分</dt><dd>{{ store.currentScore }}</dd></div>
        <div><dt>目标分</dt><dd>{{ store.targetScore }}</dd></div>
        <div><dt>距考试</dt><dd>{{ store.daysUntilExam }} 天</dd></div>
      </dl>
    </section>

    <section class="progress-grid three">
      <el-card shadow="never" class="progress-card">
        <template #header>
          <div class="card-heading">
            <h3>阶段轨迹</h3>
            <span>第 {{ store.currentStage }} / 4 阶段</span>
          </div>
        </template>
        <div class="milestone-list">
          <div
            v-for="stage in store.planMilestones"
            :key="stage.id"
            class="milestone-row"
            :class="stage.status"
          >
            <span class="milestone-index">
              <el-icon v-if="stage.status === 'completed'"><Check /></el-icon>
              <template v-else>{{ stage.id }}</template>
            </span>
            <div class="milestone-copy">
              <div class="milestone-top">
                <strong>{{ stage.name }}</strong>
                <el-tag size="small" effect="plain" :type="statusType(stage.status)">{{ statusLabel(stage.status) }}</el-tag>
              </div>
              <small>{{ stage.startDate }} ~ {{ stage.endDate }}</small>
              <p>{{ stage.target }}</p>
            </div>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="progress-card">
        <template #header>
          <div class="card-heading">
            <h3>复习队列</h3>
            <span>{{ store.reviewStats.total }} 项</span>
          </div>
        </template>
        <div class="review-stats">
          <span><b>{{ store.reviewStats.due }}</b>待复习</span>
          <span><b>{{ store.reviewStats.scheduled }}</b>已排期</span>
          <span><b>{{ store.reviewStats.stabilized }}</b>有进展</span>
        </div>
        <div v-if="visibleReviews.length" class="review-list">
          <div v-for="item in visibleReviews" :key="item.key" class="review-row" :class="{ due: isDue(item) }">
            <div>
              <strong>{{ item.knowledgeName }}</strong>
              <small>{{ item.subject }} · 下次 {{ item.nextReviewDate || '—' }} · 连续掌握 {{ item.masteryHits || 0 }}/3</small>
            </div>
            <el-tag v-if="isDue(item)" type="warning" size="small" effect="plain">今日到期</el-tag>
            <el-tag v-else size="small" effect="plain">已排期</el-tag>
          </div>
        </div>
        <el-empty v-else description="暂无复习项，阶段测试错题会自动进入这里" :image-size="64" />
        <el-button v-if="store.reviewStats.total" class="review-action" text type="primary" @click="router.push('/plan')">
          去学习路线处理
        </el-button>
      </el-card>

      <el-card shadow="never" class="progress-card">
        <template #header>
          <div class="card-heading">
            <h3>阶段测试记录</h3>
            <span>{{ store.stageTests.length }} 次</span>
          </div>
        </template>
        <div v-if="sortedTests.length" class="test-list">
          <div v-for="(test, index) in sortedTests" :key="`${test.stage}-${test.date}-${index}`" class="test-row">
            <div class="test-main">
              <span>阶段 {{ test.stage }}</span>
              <strong>{{ test.accuracy ?? Math.round((test.score || 0) / 450 * 100) }}% 正确率</strong>
              <small>{{ test.date }}</small>
            </div>
            <div class="test-meta">
              <el-tag :type="test.passed ? 'success' : 'warning'" size="small">
                {{ test.passed ? '达标' : '建议复习' }}
              </el-tag>
              <el-tag v-if="test.advancedWithoutPass" type="danger" size="small" effect="plain">跳级</el-tag>
            </div>
            <p v-if="test.weakKnowledge" class="test-weak">薄弱：{{ test.weakKnowledge }}</p>
            <p v-else-if="test.knowledgeCoverage?.length" class="test-weak">
              覆盖 {{ test.knowledgeCoverage.length }} 个知识点
            </p>
          </div>
        </div>
        <el-empty v-else description="完成阶段测试后，这里会形成成绩轨迹" :image-size="64" />
      </el-card>
    </section>

    <section class="progress-grid">
      <el-card shadow="never" class="progress-card">
        <template #header>
          <div class="card-heading">
            <h3>分科基础</h3>
            <span>诊断基线</span>
          </div>
        </template>
        <div class="subject-bars">
          <div v-for="subject in subjects" :key="subject">
            <div>
              <strong>{{ subject }}</strong>
              <span>{{ store.diagnostic.subjectScores[subject] || 0 }} / 150</span>
            </div>
            <el-progress
              :percentage="Math.round((store.diagnostic.subjectScores[subject] || 0) / 150 * 100)"
              :stroke-width="9"
              :show-text="false"
            />
          </div>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useApplicationStore } from '../stores/application'
import { fmtDate } from '../data/planner'

const router = useRouter()
const store = useApplicationStore()

const completedTasks = computed(() => store.tasks.filter(item => item.done).length)
const currentStage = computed(() => store.stages.find(item => item.id === store.currentStage))
const subjects = computed(() => store.selectedMajor?.subjects || [])
const today = fmtDate(new Date())

const isDue = (item) => !item.nextReviewDate || item.nextReviewDate <= today

const visibleReviews = computed(() => {
  const queue = store.reviewQueue || []
  const due = queue.filter(isDue)
  const scheduled = queue.filter(item => !isDue(item))
  return [...due, ...scheduled].slice(0, 8)
})

const sortedTests = computed(() =>
  [...(store.stageTests || [])].sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')))
)

const statusLabel = (status) => ({ completed: '已完成', active: '进行中', pending: '未开始' })[status] || status
const statusType = (status) => ({ completed: 'success', active: 'primary', pending: 'info' })[status] || 'info'
</script>

<style scoped lang="less" src="../styles/views/Progress.less"></style>
