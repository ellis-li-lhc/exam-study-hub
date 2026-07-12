import test from 'node:test'
import assert from 'node:assert/strict'

import { buildStageQuestions, summarizeStageCoverage } from './stageTest.js'

function makeGroup(subject, id, name, questionCount = 3) {
  return {
    id,
    subject,
    name,
    questions: Array.from({ length: questionCount }, (_, i) => ({
      id: `${id}-q${i + 1}`,
      stem: `${name} 题 ${i + 1}`,
      options: ['甲', '乙', '丙', '丁'],
      answer: 'A',
    })),
  }
}

const groups = [
  makeGroup('政治', 'p1', '哲学', 3),
  makeGroup('政治', 'p2', '近代史', 3),
  makeGroup('英语', 'e1', '时态', 3),
  makeGroup('英语', 'e2', '词汇', 3),
  makeGroup('高等数学（二）', 'm1', '极限', 3),
]

test('buildStageQuestions prioritizes focus points over group index slicing', () => {
  const questions = buildStageQuestions({
    stageId: 1,
    focusPoints: [
      { subject: '英语', id: 'e2', name: '词汇' },
      { subject: '政治', id: 'p2', name: '近代史' },
    ],
    groups,
    subjects: ['政治', '英语', '高等数学（二）'],
    limit: 4,
    perKnowledge: 2,
  })

  assert.equal(questions.length, 4)
  const names = new Set(questions.map(q => q.knowledgeName))
  assert.ok(names.has('词汇'))
  assert.ok(names.has('近代史'))
  // 不应只落到各组的第一组「哲学 / 时态」
  assert.equal(questions.filter(q => q.knowledgeName === '哲学').length, 0)
})

test('buildStageQuestions respects limit and perKnowledge', () => {
  const questions = buildStageQuestions({
    stageId: 2,
    focusPoints: [
      { subject: '政治', id: 'p1', name: '哲学' },
      { subject: '英语', id: 'e1', name: '时态' },
      { subject: '高等数学（二）', id: 'm1', name: '极限' },
    ],
    groups,
    subjects: ['政治', '英语', '高等数学（二）'],
    limit: 8,
    perKnowledge: 2,
  })

  assert.ok(questions.length <= 8)
  const byKnowledge = questions.reduce((acc, q) => {
    acc[q.knowledgeName] = (acc[q.knowledgeName] || 0) + 1
    return acc
  }, {})
  Object.values(byKnowledge).forEach(count => assert.ok(count <= 2))
})

test('buildStageQuestions returns empty when question bank unavailable', () => {
  const questions = buildStageQuestions({
    stageId: 1,
    focusPoints: [{ subject: '英语', name: '时态' }],
    groups: [],
    subjects: ['英语'],
  })
  assert.deepEqual(questions, [])
})

test('buildStageQuestions prefers questions not marked correct in diagnosis', () => {
  const questions = buildStageQuestions({
    stageId: 1,
    focusPoints: [{ subject: '政治', id: 'p1', name: '哲学' }],
    groups,
    subjects: ['政治'],
    answerDetails: [
      { questionId: 'p1-q1', correct: true },
      { questionId: 'p1-q2', correct: true },
    ],
    limit: 2,
    perKnowledge: 2,
  })

  assert.equal(questions.length, 2)
  // q1/q2 已在诊断答对，应优先抽到 q3，再回退
  assert.equal(questions[0].id, 'p1-q3')
})

test('summarizeStageCoverage groups by knowledge point', () => {
  const coverage = summarizeStageCoverage(
    [
      { id: 'a', subject: '英语', knowledgeName: '时态', answer: 'A' },
      { id: 'b', subject: '英语', knowledgeName: '时态', answer: 'B' },
      { id: 'c', subject: '政治', knowledgeName: '哲学', answer: 'A' },
    ],
    { a: 'A', b: 'A', c: 'A' }
  )

  assert.equal(coverage.length, 2)
  const tense = coverage.find(item => item.knowledgeName === '时态')
  assert.equal(tense.total, 2)
  assert.equal(tense.correct, 1)
  assert.equal(tense.wrong, 1)
})
