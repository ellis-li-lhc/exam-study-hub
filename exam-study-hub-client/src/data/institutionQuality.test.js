import test from 'node:test'
import assert from 'node:assert/strict'

import {
  hasMeaningfulValue,
  institutionDataProfile,
  latestReferenceScore,
  matchedPlansForMajor,
  validScores,
} from './institutionQuality.js'

test('validScores ignores null-like values instead of converting them to 0', () => {
  const school = {
    scores: [
      { year: 2024, score: null },
      { year: 2025, score: '118' },
      { year: 2023, score: undefined },
    ],
  }

  assert.deepEqual(validScores(school).map(item => item.score), [118])
  assert.equal(latestReferenceScore(school).score, 118)
})

test('latestReferenceScore returns the newest valid reference line', () => {
  const school = {
    scores: [
      { year: 2023, score: 121 },
      { year: 2025, score: 117 },
      { year: 2024, score: 119 },
    ],
  }

  assert.deepEqual(latestReferenceScore(school), { year: 2025, score: 117 })
})

test('matchedPlansForMajor only trusts exact major plans', () => {
  const school = {
    majorMatch: 'exact',
    plans: [
      { major_name: '软件工程', plan_count: 4 },
      { major_name: '计算机科学与技术', plan_count: 8 },
    ],
  }

  assert.equal(matchedPlansForMajor(school, '软件工程').length, 1)
  assert.equal(matchedPlansForMajor({ ...school, majorMatch: 'category' }, '软件工程').length, 0)
})

test('institutionDataProfile marks exact plan plus verified score as high confidence', () => {
  const profile = institutionDataProfile({
    majorMatch: 'exact',
    tuition: 2400,
    teachingSite: '以院校招生简章为准',
    degree: '以院校学位授予要求为准',
    source: { confidence: 'verified' },
    plans: [{ major_name: '软件工程', plan_count: 4 }],
    scores: [{ year: 2025, score: 117 }],
  }, { name: '软件工程' })

  assert.equal(profile.level, 'verified')
  assert.equal(profile.label, '高可信')
  assert.equal(profile.completed, 4)
  assert.equal(profile.checks.find(item => item.key === 'plan').ok, true)
  assert.equal(profile.checks.find(item => item.key === 'rules').ok, false)
})

test('institutionDataProfile explains category-only schools as reference data', () => {
  const profile = institutionDataProfile({
    majorMatch: 'category',
    source: { confidence: 'verified' },
    scores: [{ year: 2025, score: 118 }],
  }, { name: '软件工程' })

  assert.equal(profile.level, 'reference')
  assert.equal(profile.label, '可参考')
  assert.equal(profile.checks.find(item => item.key === 'plan').ok, false)
})

test('hasMeaningfulValue treats UI fallback copy as incomplete data', () => {
  assert.equal(hasMeaningfulValue('以院校招生简章为准'), false)
  assert.equal(hasMeaningfulValue('—'), false)
  assert.equal(hasMeaningfulValue('郑州教学点'), true)
})
