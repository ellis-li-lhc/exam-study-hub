import test from 'node:test'
import assert from 'node:assert/strict'

import {
  advanceReviewItem,
  buildDailyTasks,
  buildStageFocusPlan,
  buildWeaknessBacklog,
  fmtDate,
  getExamDate,
  resolveTaskMode,
} from './planner.js'

test('buildWeaknessBacklog ranks lower mastery and larger score gaps first', () => {
  const backlog = buildWeaknessBacklog([
    {
      name: '英语',
      gap: 8,
      mastery: 70,
      knowledgePoints: [{ id: 'vocab', name: '词汇辨析', mastery: 35, correct: 1, total: 5 }],
    },
    {
      name: '高等数学（一）',
      gap: 28,
      mastery: 45,
      knowledgePoints: [{ id: 'limit', name: '极限计算', mastery: 20, correct: 0, total: 4 }],
    },
  ])

  assert.equal(backlog[0].subject, '高等数学（一）')
  assert.equal(backlog[0].name, '极限计算')
  assert.equal(backlog[0].severity, 'urgent')
})

test('buildStageFocusPlan uses diagnostic weak points instead of static stage copy', () => {
  const stages = [
    { id: 1, title: '基础阶段', weeks: 4 },
    { id: 2, title: '专项阶段', weeks: 4 },
  ]
  const backlog = [
    { subject: '高等数学（一）', name: '极限计算', mastery: 20, reason: '掌握度 20%' },
    { subject: '英语', name: '词汇辨析', mastery: 55, reason: '掌握度 55%' },
  ]

  const plan = buildStageFocusPlan(stages, backlog)

  assert.match(plan[0].focusSummary, /极限计算/)
  assert.deepEqual(plan[0].focusPoints.map(item => item.name), ['极限计算', '词汇辨析'])
})

test('buildDailyTasks puts stage-test review items before new focus tasks', () => {
  const tasks = buildDailyTasks({
    currentStage: 1,
    weekdayHours: 2,
    weekendHours: 4,
    date: '2026-07-06',
    reviewQueue: [{ subject: '英语', knowledgeName: '动词时态' }],
    focusPoints: [{ subject: '高等数学（一）', name: '极限计算', mastery: 20, reason: '掌握度 20%' }],
    subjectTargets: [{
      name: '政治',
      knowledgePoints: [{ name: '马克思主义哲学', mastery: 40 }],
    }],
  })

  assert.equal(tasks[0].title, '复习薄弱点：动词时态')
  assert.equal(tasks[1].title, '极限计算 · 基础概念与高频题')
  assert.equal(tasks.every(task => task.duration > 0), true)
})

test('buildDailyTasks only schedules review items when their review date is due', () => {
  const tasks = buildDailyTasks({
    currentStage: 2,
    weekdayHours: 2,
    weekendHours: 4,
    date: '2026-07-06',
    reviewQueue: [
      { key: '英语:动词时态', subject: '英语', knowledgeName: '动词时态', nextReviewDate: '2026-07-07', priority: 120 },
      { key: '政治:哲学', subject: '政治', knowledgeName: '哲学', nextReviewDate: '2026-07-06', priority: 90 },
    ],
    focusPoints: [{ subject: '高等数学（一）', name: '极限计算', mastery: 20, reason: '掌握度 20%' }],
    subjectTargets: [],
  })

  assert.equal(tasks[0].title, '复习薄弱点：哲学')
  assert.equal(tasks.some(task => task.title.includes('动词时态')), false)
})

test('advanceReviewItem delays review and marks item mastered after three successful rounds', () => {
  const first = advanceReviewItem({
    key: '英语:动词时态',
    subject: '英语',
    knowledgeName: '动词时态',
    masteryHits: 0,
    priority: 120,
  }, { date: '2026-07-06', passed: true })
  const second = advanceReviewItem(first, { date: '2026-07-07', passed: true })
  const third = advanceReviewItem(second, { date: '2026-07-10', passed: true })

  assert.equal(first.masteryHits, 1)
  assert.equal(first.nextReviewDate, '2026-07-07')
  assert.equal(second.nextReviewDate, '2026-07-10')
  assert.equal(third.mastered, true)
})

test('resolveTaskMode switches into sprint style near the exam date', () => {
  assert.equal(resolveTaskMode({ currentStage: 1, daysUntilExam: 112 }).taskStage, 1)
  assert.equal(resolveTaskMode({ currentStage: 1, daysUntilExam: 45 }).taskStage, 3)
  assert.equal(resolveTaskMode({ currentStage: 2, daysUntilExam: 20 }).taskStage, 4)
})

test('getExamDate keeps the target day before the final October weekend buffer', () => {
  assert.equal(fmtDate(getExamDate(2026)), '2026-10-24')
})
