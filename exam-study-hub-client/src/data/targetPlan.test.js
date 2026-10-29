import test from 'node:test'
import assert from 'node:assert/strict'

import { verifiedReferenceScore } from './targetPlan.js'

test('target planning refuses to infer a score without a verified matching reference', () => {
  assert.equal(verifiedReferenceScore({ scores: [{ year: 2025, score: 117 }] }, '计算机科学与技术'), null)
  assert.equal(verifiedReferenceScore({ source: { confidence: 'verified' }, scores: [] }, '计算机科学与技术'), null)
})

test('target planning uses the verified latest reference line', () => {
  const school = {
    source: { confidence: 'verified' },
    scores: [{ year: 2024, score: 130 }, { year: 2025, score: 117 }],
  }
  assert.equal(verifiedReferenceScore(school, '计算机科学与技术'), 117)
})
