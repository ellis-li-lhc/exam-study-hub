// 计划生成（纯函数）：达标日期里程碑 + 每日任务，均由档案/诊断动态推导，
// 不写死。store 负责把当前状态喂进来、拿结果回填。

// —— 日期小工具 ——
function toDate(value) {
  return value instanceof Date ? value : new Date(value)
}
function addDays(date, n) {
  const r = new Date(date)
  r.setDate(r.getDate() + n)
  return r
}
function fmt(date) {
  const d = toDate(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
// 对外暴露：按本地时区格式化为 YYYY-MM-DD（避免 toISOString 在东八区把日期减一天）。
export function fmtDate(date) {
  return fmt(date)
}
function daysBetween(a, b) {
  return Math.round((toDate(b) - toDate(a)) / 86400000)
}

// 成人高考全国统考一般在 10 月最后一个完整周末。这里取当年 10 月的第 4 个周六作为参考考试日。
export function getExamDate(year) {
  const oct1 = new Date(year, 9, 1)            // 月份从 0 开始，9 = 十月
  const firstSatOffset = (6 - oct1.getDay() + 7) % 7
  const fourthSat = 1 + firstSatOffset + 21    // 第 1 个周六再加 3 周
  return new Date(year, 9, fourthSat)
}

// 把四个阶段按「建议周数」铺到 [开始日, 考试日] 区间上，算出每个阶段的起止日期。
// 关键点：未来阶段始终从「今天」往后铺——今天越晚，剩余阶段自动压缩，
// 这就是计划随进度/测试结果动态纠偏（重排期）的体现。
export function buildMilestones(stageTemplates, { startDate, examDate, currentStage, today }) {
  const start = toDate(startDate)
  const exam = toDate(examDate)
  const now = toDate(today)
  const anchor = now > start ? now : start

  const out = []

  // 已完成阶段：把 [开始日, 今天] 按其周数比例回填，仅用于展示已走过的时间轴。
  const doneStages = stageTemplates.filter(s => s.id < currentStage)
  const doneWeeks = doneStages.reduce((sum, s) => sum + s.weeks, 0) || 1
  const pastDays = Math.max(0, daysBetween(start, anchor))
  let cursor = start
  doneStages.forEach(s => {
    const days = Math.round(pastDays * s.weeks / doneWeeks)
    const end = addDays(cursor, days)
    out.push({ ...s, startDate: fmt(cursor), endDate: fmt(end), status: 'completed' })
    cursor = end
  })

  // 当前 + 未来阶段：从今天起，按剩余周数比例铺到考试日；最后一个阶段直接顶到考试日。
  const remaining = stageTemplates.filter(s => s.id >= currentStage)
  const remWeeks = remaining.reduce((sum, s) => sum + s.weeks, 0) || 1
  const totalDays = Math.max(7, daysBetween(anchor, exam))
  cursor = anchor
  remaining.forEach((s, index) => {
    const days = index === remaining.length - 1
      ? Math.max(1, daysBetween(cursor, exam))
      : Math.round(totalDays * s.weeks / remWeeks)
    const end = addDays(cursor, days)
    out.push({
      ...s,
      startDate: fmt(cursor),
      endDate: fmt(end),
      status: s.id === currentStage ? 'active' : 'pending'
    })
    cursor = end
  })

  return out.sort((a, b) => a.id - b.id)
}

// 不同阶段对应的任务风格（决定每日任务的措辞、类型与单题时长）。
const STAGE_TASK = {
  1: { type: '基础训练', verb: '基础概念与高频题', minutes: 40 },
  2: { type: '专项练习', verb: '专项突破', minutes: 45 },
  3: { type: '真题训练', verb: '历年真题演练', minutes: 50 },
  4: { type: '模考冲刺', verb: '限时模考', minutes: 55 }
}

// 生成「今天」的任务清单：
// 1) 先排阶段测试沉淀下来的复习项（动态纠偏）；
// 2) 再按各科最薄弱知识点、跨科目轮排，填满当天时间预算；
// 工作日/周末用不同的时长预算。done 状态由 store 维护。
export function buildDailyTasks({ subjectTargets, currentStage, weekdayHours, weekendHours, reviewQueue, date }) {
  const d = toDate(date)
  const isWeekend = [0, 6].includes(d.getDay())
  const budget = Math.max(60, (isWeekend ? weekendHours : weekdayHours) * 60)
  const stage = STAGE_TASK[currentStage] || STAGE_TASK[1]

  const tasks = []
  let id = 1
  let used = 0

  // 1) 复习项优先（来自阶段测试的薄弱知识点）
  ;(reviewQueue || []).forEach(item => {
    if (used >= budget) return
    tasks.push({
      id: id++,
      subject: item.subject,
      title: `复习薄弱点：${item.knowledgeName}`,
      duration: 30,
      type: '复习巩固',
      done: false,
      reviewKey: item.knowledgeName
    })
    used += 30
  })

  // 2) 各科按掌握度从低到高取知识点，跨科目轮排，填满预算
  const perSubject = (subjectTargets || []).map(st => ({
    subject: st.name,
    points: (st.knowledgePoints || []).slice().sort((a, b) => a.mastery - b.mastery)
  }))

  let added = true
  while (added && used < budget) {
    added = false
    for (const s of perSubject) {
      if (used >= budget) break
      const point = s.points.shift()
      if (!point) continue
      tasks.push({
        id: id++,
        subject: s.subject,
        title: `${point.name} · ${stage.verb}`,
        duration: stage.minutes,
        type: stage.type,
        done: false,
        mastery: point.mastery
      })
      used += stage.minutes
      added = true
    }
  }

  // 兜底：诊断未细分到知识点时，给每科一条阶段任务，保证计划不空。
  if (!tasks.length) {
    (subjectTargets || []).slice(0, 3).forEach(st => {
      tasks.push({
        id: id++,
        subject: st.name,
        title: `${st.name} · ${stage.verb}`,
        duration: stage.minutes,
        type: stage.type,
        done: false
      })
    })
  }

  return tasks
}
