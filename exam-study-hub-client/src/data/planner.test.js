import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildDailyTasks,
  buildStageFocusPlan,
  buildWeaknessBacklog,
  fmtDate,
  getExamDate,
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

test('getExamDate keeps the target day before the final October weekend buffer', () => {
  assert.equal(fmtDate(getExamDate(2026)), '2026-10-24')
})
