import test from 'node:test'
import assert from 'node:assert/strict'

import {
  hasMeaningfulValue,
  institutionDataProfile,
  latestReferenceScore,
  matchedPlansForMajor,
  referenceScoresForMajor,
  validScores,
  durationForMajor,
  normalizeInstitutionScores,
  scoresForMajorSelection,
  tuitionForPlanText,
} from './institutionQuality.js'
import { readFileSync } from 'node:fs'
import { examMajors } from './majors.js'

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

test('referenceScoresForMajor matches Guangdong plan group to its投档 line', () => {
  const school = {
    majorMatch: 'exact',
    plans: [{ major_name: '工商管理', category_code: '103' }],
    scores: [
      { year: 2025, category_code: '12101', category_name: '专升本文史中医类', score: 160 },
      { year: 2025, category_code: '11103', category_name: '专升本理工经管类', score: 102 },
    ],
  }

  assert.deepEqual(referenceScoresForMajor(school, '工商管理').map(item => item.score), [102])
  assert.equal(latestReferenceScore(school, '工商管理').score, 102)
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

test('all Guangdong selectable school and major pairs preserve their matching group through normalization', () => {
  const read = name => JSON.parse(readFileSync(new URL(`../../../exam-study-hub-server/scraped-data/${name}`, import.meta.url)))
  const plans = read('guangdong-adult-program-plan-2025.json')
  const scores = [...read('guangdong-adult-scores.json'), ...read('guangdong-adult-scores-history.json')]
  const taggedCategory = { '101': '文史中医类', '104': '法学类', '105': '教育学类' }
  let checked = 0
  for (const plan of plans) {
    const major = examMajors.find(item => item.name === plan.major_name)
    if (!major) continue
    const schoolScores = scores.filter(item => item.institution_code === plan.institution_code)
    const school = {
      majorMatch: 'exact',
      plans: plans.filter(item => item.institution_code === plan.institution_code),
      scores: normalizeInstitutionScores(schoolScores.map(item => ({ ...item, major_category: taggedCategory[item.category_code.slice(-3)] ?? null }))),
    }
    const actual = scoresForMajorSelection(school, major)
    const expected = schoolScores.filter(item => item.category_code.endsWith(plan.category_code) && item.score != null)
    assert.deepEqual(actual.map(s => [s.year, s.category_code, s.score]).sort(), expected.map(s => [s.year, s.category_code, s.score]).sort())
    assert.ok(actual.some(s => s.year === 2025))
    checked++
  }
  assert.equal(checked, 547)
})

test('missing matching group never falls back to another subjects reference line', () => {
  const school = { majorMatch: 'exact', plans: [{ major_name: '工商管理', category_code: '103' }], scores: [{ year: 2025, category_code: '12101', score: 180 }] }
  assert.deepEqual(referenceScoresForMajor(school, '工商管理'), [])
  assert.deepEqual(referenceScoresForMajor(school, '不存在的专业'), [])
})

test('latest reference line uses the newest year instead of an older higher score', () => {
  assert.equal(latestReferenceScore({ scores: [{ year: 2023, score: 188 }, { year: 2025, score: 100 }] }).score, 100)
})

test('duration uses verified facts and respects major-specific differences', () => {
  const school = { supplementalData: { facts: [
    { year: 2025, field: 'duration_by_major', value: { 消防工程: 2.5, 消防指挥: 3 }, review_status: 'verified_text' },
    { year: 2025, field: 'duration_years', value: 9, review_status: 'ocr_requires_review' },
  ] } }
  assert.equal(durationForMajor(school, '消防工程'), '2.5 年')
  assert.equal(durationForMajor(school, '消防指挥'), '3 年')
  assert.equal(durationForMajor(school, '其他专业'), '暂未获取')
})

test('tuition display preserves total and annual charges and unknown amounts', () => {
  assert.equal(tuitionForPlanText({ tuition_amount: 7200, tuition_unit: 'total' }), '总学费 ¥7200')
  assert.equal(tuitionForPlanText({ tuition_amount: 3960, tuition_unit: 'per_academic_year' }), '¥3960/学年')
  assert.equal(tuitionForPlanText({ tuition_raw: '按物价部门核定标准执行' }), '按物价部门核定标准执行')
})
