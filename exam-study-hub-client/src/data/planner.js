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

// 成人高考统考一般在 10 月最后一个周末。这里把“目标考期/达标基准日”取为
// 10 月倒数第二个周六（比实际考试提前约一周，给最后冲刺与意外留出缓冲）。
export function getExamDate(year) {
  const oct31 = new Date(year, 9, 31)              // 月份从 0 开始，9 = 十月
  const offsetToLastSat = (oct31.getDay() - 6 + 7) % 7  // 从 10/31 往回到最近周六的天数
  const lastSat = 31 - offsetToLastSat             // 10 月最后一个周六（≈实际考试）
  return new Date(year, 9, lastSat - 7)            // 倒数第二个周六（目标达标日）
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

const REVIEW_INTERVALS = [1, 3, 7]
const REVIEW_MASTERED_HITS = 3

const STAGE_FOCUS = {
  1: {
    title: '补齐最低掌握度',
    reason: '优先处理诊断中掌握度最低的基础点，先把送分区稳住。',
    action: '基础补缺'
  },
  2: {
    title: '集中专项突破',
    reason: '围绕分差贡献最大的薄弱点做专项训练，拉开提分空间。',
    action: '专项突破'
  },
  3: {
    title: '真题场景迁移',
    reason: '把薄弱点放进历年真题语境里练，减少会概念但不会做题的断层。',
    action: '真题套用'
  },
  4: {
    title: '模考复盘稳定',
    reason: '用阶段错题和低稳定性知识点做冲刺复盘，压低临场波动。',
    action: '模考复盘'
  }
}

function uniqueBy(items, keyFn) {
  const seen = new Set()
  return items.filter(item => {
    const key = keyFn(item)
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

export function reviewKeyFor(point = {}) {
  const subject = String(point.subject || '综合')
  const knowledgeName = String(point.knowledgeName || point.name || point.reviewKey || '')
  return `${subject}:${knowledgeName}`
}

export function normalizeReviewItem(item, fallbackDate = fmt(new Date())) {
  const subject = item?.subject || '综合'
  const knowledgeName = item?.knowledgeName || item?.name || item?.reviewKey || ''
  const key = item?.key || reviewKeyFor({ subject, knowledgeName })
  const masteryHits = Math.max(0, Number(item?.masteryHits || 0))
  const priority = Number.isFinite(Number(item?.priority)) ? Number(item.priority) : 100
  return {
    key,
    subject,
    knowledgeName,
    source: item?.source || 'stage-test',
    addedStage: item?.addedStage ?? null,
    addedDate: item?.addedDate || fallbackDate,
    nextReviewDate: item?.nextReviewDate || fallbackDate,
    masteryHits,
    priority,
    lastDoneDate: item?.lastDoneDate || null,
    lastResult: item?.lastResult || null,
  }
}

export function normalizeReviewQueue(queue = [], fallbackDate = fmt(new Date())) {
  const map = new Map()
  queue.forEach(item => {
    const normalized = normalizeReviewItem(item, fallbackDate)
    if (!normalized.knowledgeName) return
    const existing = map.get(normalized.key)
    if (!existing || normalized.priority > existing.priority || normalized.nextReviewDate < existing.nextReviewDate) {
      map.set(normalized.key, normalized)
    }
  })
  return [...map.values()].sort((a, b) =>
    String(a.nextReviewDate).localeCompare(String(b.nextReviewDate)) ||
    b.priority - a.priority ||
    a.knowledgeName.localeCompare(b.knowledgeName, 'zh')
  )
}

export function advanceReviewItem(item, { date = fmt(new Date()), passed = true } = {}) {
  const normalized = normalizeReviewItem(item, date)
  if (!passed) {
    return {
      ...normalized,
      masteryHits: 0,
      priority: Math.min(140, normalized.priority + 25),
      nextReviewDate: fmt(addDays(date, 1)),
      lastDoneDate: date,
      lastResult: 'wrong',
    }
  }

  const masteryHits = normalized.masteryHits + 1
  if (masteryHits >= REVIEW_MASTERED_HITS) {
    return {
      ...normalized,
      masteryHits,
      priority: 0,
      nextReviewDate: null,
      lastDoneDate: date,
      lastResult: 'mastered',
      mastered: true,
    }
  }

  return {
    ...normalized,
    masteryHits,
    priority: Math.max(20, normalized.priority - 35),
    nextReviewDate: fmt(addDays(date, REVIEW_INTERVALS[masteryHits - 1] || 7)),
    lastDoneDate: date,
    lastResult: 'passed',
  }
}

export function resolveTaskMode({ currentStage = 1, daysUntilExam = 999 } = {}) {
  const stage = Number(currentStage || 1)
  const days = Number(daysUntilExam)
  if (Number.isFinite(days) && days <= 30) {
    return {
      key: 'sprint',
      label: '冲刺模式',
      taskStage: 4,
      description: '距考试 30 天内，今日任务自动偏向限时模考、错题复盘和稳定输出。',
    }
  }
  if (Number.isFinite(days) && days <= 60) {
    return {
      key: 'exam-transfer',
      label: '真题强化',
      taskStage: Math.max(stage, 3),
      description: '距考试 60 天内，计划会减少纯铺知识点，优先把薄弱项放进真题场景。',
    }
  }
  return {
    key: 'adaptive',
    label: '诊断驱动',
    taskStage: stage,
    description: '按诊断薄弱项、阶段测试和复习队列生成今日任务。',
  }
}

export function buildWeaknessBacklog(subjectTargets = []) {
  const points = subjectTargets.flatMap(subject => {
    const subjectGap = Math.max(0, Number(subject.gap || 0))
    const sourcePoints = subject.knowledgePoints?.length
      ? subject.knowledgePoints
      : [{ id: subject.name, name: `${subject.name}综合巩固`, mastery: subject.mastery, correct: null, total: null }]
    return sourcePoints.map(point => {
      const mastery = Number(point.mastery ?? subject.mastery ?? 0)
      const weakness = Math.max(0, 100 - mastery)
      const volumeWeight = Number(point.total || 0) > 0 ? Math.min(Number(point.total), 10) * 1.5 : 3
      const priority = Math.round(weakness * 1.4 + Math.min(subjectGap, 80) * 0.55 + volumeWeight)
      return {
        id: point.id || `${subject.name}-${point.name}`,
        subject: subject.name,
        name: point.name,
        mastery,
        correct: point.correct,
        total: point.total,
        gap: subjectGap,
        priority,
        severity: mastery < 40 ? 'urgent' : mastery < 60 ? 'weak' : mastery < 75 ? 'watch' : 'steady',
        reason: `掌握度 ${mastery}%${subjectGap ? `，该科还需提升 ${subjectGap} 分` : ''}`
      }
    })
  })
  return uniqueBy(points, item => `${item.subject}:${item.id}:${item.name}`)
    .sort((a, b) => b.priority - a.priority || a.mastery - b.mastery)
}

export function buildStageFocusPlan(stageTemplates, weaknessBacklog = []) {
  const fallback = weaknessBacklog.slice(0, 3)
  return stageTemplates.map(stage => {
    const config = STAGE_FOCUS[stage.id] || STAGE_FOCUS[1]
    const pool = stage.id === 1
      ? weaknessBacklog.filter(point => point.mastery < 60)
      : stage.id === 2
        ? weaknessBacklog.filter(point => point.mastery < 75)
        : weaknessBacklog
    const focusPoints = (pool.length ? pool : fallback).slice(0, stage.id >= 3 ? 4 : 5)
    const top = focusPoints[0]
    const focusSummary = top
      ? `${top.subject}「${top.name}」优先，${top.reason}`
      : '完成诊断后自动生成阶段重点'
    return {
      ...stage,
      focusTitle: config.title,
      focusReason: config.reason,
      focusAction: config.action,
      focusSummary,
      focusPoints
    }
  })
}

// 生成「今天」的任务清单：
// 1) 先排阶段测试沉淀下来的复习项（动态纠偏）；
// 2) 再按各科最薄弱知识点、跨科目轮排，填满当天时间预算；
// 工作日/周末用不同的时长预算。done 状态由 store 维护。
export function buildDailyTasks({ subjectTargets, currentStage, weekdayHours, weekendHours, reviewQueue, focusPoints, date, daysUntilExam }) {
  const d = toDate(date)
  const isWeekend = [0, 6].includes(d.getDay())
  const budget = Math.max(60, (isWeekend ? weekendHours : weekdayHours) * 60)
  const taskMode = resolveTaskMode({ currentStage, daysUntilExam })
  const taskStage = taskMode.taskStage
  const stage = STAGE_TASK[taskStage] || STAGE_TASK[1]
  const isSprintTask = taskMode.key !== 'adaptive'

  const tasks = []
  let id = 1
  let used = 0
  const canFit = duration => used === 0 || used + duration <= budget

  // 1) 复习项优先（来自阶段测试的薄弱知识点）；未到 nextReviewDate 的错题进入后续任务。
  const dueReviews = normalizeReviewQueue(reviewQueue || [], fmt(d))
    .filter(item => !item.nextReviewDate || item.nextReviewDate <= fmt(d))
    .sort((a, b) => b.priority - a.priority || a.masteryHits - b.masteryHits)
  dueReviews.forEach(item => {
    const duration = taskStage >= 3 ? 35 : 30
    if (!canFit(duration)) return
    tasks.push({
      id: id++,
      subject: item.subject,
      title: `${taskStage >= 3 ? '错题复盘' : '复习薄弱点'}：${item.knowledgeName}`,
      duration,
      type: item.masteryHits ? `复习巩固 · 第 ${item.masteryHits + 1} 轮` : '复习巩固',
      done: false,
      reviewKey: item.key,
      reviewDueDate: item.nextReviewDate,
      masteryHits: item.masteryHits,
      priority: item.priority,
      source: item.source,
      planMode: taskMode.key,
      modeLabel: taskMode.label,
      sprint: isSprintTask,
    })
    used += duration
  })

  // 2) 当前阶段的诊断重点优先进入今日任务。
  ;(focusPoints || []).forEach(point => {
    if (!canFit(stage.minutes)) return
    tasks.push({
      id: id++,
      subject: point.subject,
      title: `${point.name} · ${stage.verb}`,
      duration: stage.minutes,
      type: stage.type,
      done: false,
      mastery: point.mastery,
      focus: true,
      reason: point.reason,
      planMode: taskMode.key,
      modeLabel: taskMode.label,
      sprint: isSprintTask,
    })
    used += stage.minutes
  })

  const usedFocusKeys = new Set((focusPoints || []).map(point => `${point.subject}:${point.name}`))

  // 3) 各科按掌握度从低到高取知识点，跨科目轮排，填满预算
  const perSubject = (subjectTargets || []).map(st => ({
    subject: st.name,
    points: (st.knowledgePoints || [])
      .filter(point => !usedFocusKeys.has(`${st.name}:${point.name}`))
      .slice()
      .sort((a, b) => a.mastery - b.mastery)
  }))

  let added = true
  while (added && used < budget) {
    added = false
    for (const s of perSubject) {
      if (used >= budget) break
      if (!canFit(stage.minutes)) break
      const point = s.points.shift()
      if (!point) continue
      tasks.push({
        id: id++,
        subject: s.subject,
        title: `${point.name} · ${stage.verb}`,
        duration: stage.minutes,
        type: stage.type,
        done: false,
        mastery: point.mastery,
        planMode: taskMode.key,
        modeLabel: taskMode.label,
        sprint: isSprintTask,
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
        done: false,
        planMode: taskMode.key,
        modeLabel: taskMode.label,
        sprint: isSprintTask,
      })
    })
  }

  return tasks
}
