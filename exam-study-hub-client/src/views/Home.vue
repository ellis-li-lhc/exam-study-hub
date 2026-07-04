<template>
  <div class="dashboard-page">
    <section class="welcome-panel">
      <div class="welcome-copy">
        <span class="section-kicker">{{ store.profile.examYear }} 成人高考专升本</span>
        <h2>{{ greeting }}，今天从最重要的一步开始。</h2>
        <p v-if="store.profileComplete">当前目标是 {{ provinceText }}的{{ store.selectedMajor?.name }}。先完成诊断，再让学习时间真正花在能提分的地方。</p>
        <p v-else>还没有建立报考档案。先选定报考省份和报考类别，系统才能帮你匹配招生院校、生成入学诊断和学习计划。</p>
        <div class="welcome-actions">
          <el-button type="primary" size="large" @click="router.push(nextAction.path)">
            {{ nextAction.label }}<el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
          <el-button size="large" @click="router.push('/profile')">调整档案</el-button>
        </div>
      </div>
      <div class="score-orbit">
        <el-progress type="dashboard" :percentage="scorePercentage" :width="154" :stroke-width="12" color="#1d4ed8">
          <template #default>
            <strong>{{ store.diagnosisComplete ? store.currentScore : '--' }}</strong>
            <span>/ {{ store.targetScore }} 目标分</span>
          </template>
        </el-progress>
        <small>{{ store.diagnosisComplete ? `还差 ${store.scoreGap} 分` : '完成诊断后计算差距' }}</small>
      </div>
    </section>

    <section class="metrics-grid">
      <article v-for="metric in metrics" :key="metric.label" class="metric-card">
        <span class="metric-icon" :class="metric.tone"><el-icon><component :is="metric.icon" /></el-icon></span>
        <div><p>{{ metric.label }}</p><strong>{{ metric.value }}</strong><small>{{ metric.note }}</small></div>
      </article>
    </section>

    <section class="dashboard-grid">
      <el-card shadow="never" class="journey-card">
        <template #header><div class="card-heading"><div><span class="section-kicker">你的闭环</span><h3>备考路径</h3></div><span>{{ completedFlow }}/5 已完成</span></div></template>
        <div class="journey-list">
          <button v-for="(step,index) in journey" :key="step.title" class="journey-step" :class="step.status" @click="router.push(step.path)">
            <span class="step-index"><el-icon v-if="step.status === 'done'"><Check /></el-icon><template v-else>{{ index + 1 }}</template></span>
            <span class="step-copy"><strong>{{ step.title }}</strong><small>{{ step.desc }}</small></span>
            <el-icon><ArrowRight /></el-icon>
          </button>
        </div>
      </el-card>

      <el-card shadow="never" class="today-card">
        <template #header><div class="card-heading"><div><span class="section-kicker">今日节奏</span><h3>{{ store.profile.mode === 'plan' ? `${store.tasks.length} 项学习任务` : '自主学习建议' }}</h3></div><el-tag>{{ store.profile.mode === 'plan' ? '计划模式' : '自主模式' }}</el-tag></div></template>
        <template v-if="store.profile.mode === 'plan'">
          <label v-for="task in store.tasks" :key="task.id" class="mini-task" :class="{ done: task.done }">
            <el-checkbox :model-value="task.done" @change="store.toggleTask(task.id)" />
            <span><strong>{{ task.subject }}</strong><small>{{ task.title }}</small></span>
            <b>{{ task.duration }} 分</b>
          </label>
          <el-button text type="primary" @click="router.push('/plan')">查看完整学习路线</el-button>
        </template>
        <div v-else class="self-study-empty">
          <span class="metric-icon blue"><el-icon><Compass /></el-icon></span>
          <h4>从当前阶段挑一个知识点开始</h4>
          <p>系统保留阶段路线和测试，不替你安排今天几点学习。</p>
          <el-button type="primary" plain @click="router.push('/plan')">打开学习路线</el-button>
        </div>
      </el-card>
    </section>

    <el-alert title="院校与分数线来自已接入省份公开数据；江苏以院校投档线为主，河南以省控线和征集志愿备档线为参考。录取以考试院和院校当年招生简章为准。" type="info" show-icon :closable="false" />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApplicationStore } from '../stores/application'

const router = useRouter()
const store = useApplicationStore()

// 计划模式下进入首页时，确保已生成「今天」的任务（跨天会自动刷新）。
onMounted(() => store.ensureTodayTasks())

const hour = new Date().getHours()
const greeting = hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
const provinceText = computed(() => store.selectedProvinces.map(item => item.label).join('、'))
const scorePercentage = computed(() => store.diagnosisComplete ? Math.min(100, Math.round(store.currentScore / store.targetScore * 100)) : 0)
const nextAction = computed(() => !store.profileComplete
  ? { label: '建立报考档案', path: '/profile' }
  : !store.selectedInstitution
    ? { label: '选择目标院校', path: '/schools' }
    : !store.diagnosisComplete
      ? { label: '开始入学诊断', path: '/diagnosis' }
      : { label: '继续今日学习', path: '/plan' })

const metrics = computed(() => [
  { label: '可报考省份', value: `${store.selectedProvinces.length} 个`, note: provinceText.value, icon: 'Location', tone: 'blue' },
  { label: '考试科目', value: `${store.selectedMajor?.subjects.length || 0} 科`, note: store.selectedMajor?.subjects.join(' · '), icon: 'Tickets', tone: 'mint' },
  { label: '每周学习', value: `${store.weeklyHours} 小时`, note: store.profile.mode === 'plan' ? '系统自动排期' : '由你自主安排', icon: 'Clock', tone: 'amber' },
  { label: '距考试', value: `${store.daysUntilExam} 天`, note: `考试日 ${store.examDate}`, icon: 'TrendCharts', tone: 'violet' }
])

const journey = computed(() => [
  { title: '报考档案', desc: '省份、报考类别与学习模式', path: '/profile', status: store.profileComplete ? 'done' : 'active' },
  { title: '目标院校', desc: '查看学费、学制与历史分数', path: '/schools', status: store.selectedInstitution ? 'done' : store.profileComplete ? 'active' : 'pending' },
  { title: '入学诊断', desc: '评估基础、速度和错题类型', path: '/diagnosis', status: store.diagnosisComplete ? 'done' : store.selectedInstitution ? 'active' : 'pending' },
  { title: '目标分数', desc: '参考线 + 30 分安全目标', path: '/target', status: store.diagnosisComplete ? 'done' : 'pending' },
  { title: '学习与纠偏', desc: '四阶段路线和阶段测试', path: '/plan', status: store.overallProgress > 0 ? 'active' : 'pending' }
])
const completedFlow = computed(() => journey.value.filter(item => item.status === 'done').length)
</script>

<style scoped>
.dashboard-page{display:flex;flex-direction:column;gap:18px}
.welcome-panel{display:grid;grid-template-columns:minmax(0,1fr) 216px;gap:28px;align-items:center;padding:28px 30px;border:1px solid var(--line);border-radius:var(--radius-lg);background:#fff;box-shadow:var(--shadow-xs)}
.section-kicker{display:block;margin-bottom:7px;color:var(--primary);font-size:.7rem;font-weight:900;letter-spacing:.08em}
.welcome-copy h2{max-width:690px;color:var(--ink);font-size:clamp(1.45rem,2.4vw,2rem);line-height:1.28;letter-spacing:0}
.welcome-copy p{max-width:720px;margin:12px 0 22px;color:var(--text-secondary);font-size:.9rem}
.welcome-actions{display:flex;gap:10px;flex-wrap:wrap}
.score-orbit{text-align:center;padding:12px;border-left:1px solid var(--line)}
.score-orbit strong,.score-orbit span{display:block}
.score-orbit strong{color:var(--ink);font-size:2rem;line-height:1}
.score-orbit span{margin-top:6px;color:var(--text-muted);font-size:.72rem}
.score-orbit small{display:block;margin-top:-8px;color:var(--primary);font-weight:800}
.metrics-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.metric-card{display:flex;gap:12px;align-items:flex-start;padding:16px;border:1px solid var(--line);border-radius:var(--radius-md);background:#fff;box-shadow:var(--shadow-xs)}
.metric-icon{width:38px;height:38px;display:grid;place-items:center;flex:0 0 auto;border-radius:10px}
.metric-icon.blue{color:var(--primary);background:var(--primary-soft)}
.metric-icon.mint{color:var(--mint);background:var(--mint-soft)}
.metric-icon.amber{color:var(--accent);background:var(--accent-soft)}
.metric-icon.violet{color:#475569;background:#eef2f7}
.metric-card p{color:var(--text-muted);font-size:.72rem;font-weight:800}
.metric-card strong{display:block;color:var(--ink);font-size:1.18rem;line-height:1.25}
.metric-card small{display:block;color:var(--text-secondary);font-size:.72rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:170px}
.dashboard-grid{display:grid;grid-template-columns:1.08fr .92fr;gap:16px}
.journey-card,.today-card{border-radius:var(--radius-lg);border-color:var(--line)}
.card-heading{display:flex;align-items:center;justify-content:space-between;gap:14px}
.card-heading h3{color:var(--ink);font-size:1.02rem}
.card-heading>span{color:var(--text-muted);font-size:.76rem;font-weight:800}
.journey-list{display:flex;flex-direction:column;gap:6px}
.journey-step{width:100%;display:flex;align-items:center;gap:12px;padding:12px;border:1px solid transparent;border-radius:var(--radius-md);text-align:left;background:transparent;color:var(--text-muted);cursor:pointer;transition:background-color var(--ease-standard),border-color var(--ease-standard)}
.journey-step:hover{border-color:var(--line);background:var(--surface-soft)}
.journey-step.active{border-color:#cbdaf3;background:var(--primary-faint);color:var(--primary)}
.journey-step.done .step-index{color:#fff;background:var(--mint)}
.step-index{width:30px;height:30px;display:grid;place-items:center;flex:0 0 auto;border-radius:9px;font-size:.76rem;font-weight:900;background:#edf1f7}
.step-copy{flex:1;min-width:0}
.step-copy strong,.step-copy small{display:block}
.step-copy strong{color:var(--ink);font-size:.86rem}
.step-copy small{font-size:.72rem}
.mini-task{display:flex;align-items:center;gap:10px;padding:12px 0;border-bottom:1px solid var(--line);cursor:pointer}
.mini-task>span{flex:1;min-width:0}
.mini-task strong,.mini-task small{display:block}
.mini-task strong{color:var(--ink);font-size:.82rem}
.mini-task small{color:var(--text-secondary);font-size:.73rem}
.mini-task>b{color:var(--text-muted);font-size:.72rem}
.mini-task.done{opacity:.6}
.mini-task.done small{text-decoration:line-through}
.self-study-empty{text-align:center;padding:24px 10px}
.self-study-empty .metric-icon{margin:0 auto 12px}
.self-study-empty h4{color:var(--ink)}
.self-study-empty p{margin:7px auto 16px;color:var(--text-secondary);font-size:.84rem;max-width:35ch}
@media(max-width:1100px){.metrics-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:760px){.welcome-panel{grid-template-columns:1fr;padding:22px}.score-orbit{display:none}.dashboard-grid{grid-template-columns:1fr}.metrics-grid{grid-template-columns:1fr}}
</style>
