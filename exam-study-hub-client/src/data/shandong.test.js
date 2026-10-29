import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { examMajors } from './majors.js'
import { activePlansForMajor, controlScoresForMajor, durationForMajor, institutionSelectionCode, latestReferenceScore, tuitionForMajorText } from './institutionQuality.js'
import { verifiedReferenceScore } from './targetPlan.js'
import { isProvinceAvailable, matchesCityPreference, OUTSIDE_PROVINCE_CITY } from './regions.js'

const read = name => JSON.parse(readFileSync(new URL(`../../../exam-study-hub-server/scraped-data/${name}`, import.meta.url)))
const plans = read('shandong-adult-programs.json')
const controls = read('shandong-adult-control-scores.json')
const schoolFor = code => ({
  province: 'shandong', majorMatch: 'exact', activeCatalogYear: 2026,
  plans: plans.filter(plan => plan.institution_code === code), controlScores: controls,
  scores: [], source: { confidence: 'verified', line_type: '招生专业目录' },
})

test('all current Shandong course matches keep category controls separate from school scores', () => {
  let checked = 0
  for (const plan of plans.filter(row => row.year === 2026)) {
    const major = examMajors.find(row => row.name === plan.major_name)
    if (!major) continue
    const school = schoolFor(plan.institution_code)
    const lines = controlScoresForMajor(school, major.name)
    assert.equal(lines.length, 3, `${plan.institution_code}/${major.name}`)
    assert.equal(latestReferenceScore(school, major.name), null)
    assert.equal(verifiedReferenceScore(school, major.name), null)
    assert.equal(durationForMajor(school, major.name), plan.study_duration_raw)
    assert.equal(tuitionForMajorText(school, major.name), '暂未获取')
    checked++
  }
  assert.equal(checked, 629)
})

test('Shandong splits 文史 and 中医 controls and respects the changed 体育 grouping', () => {
  const tcm = controlScoresForMajor(schoolFor('111'), '中医学')
  assert.deepEqual(tcm.map(row => [row.year, row.category_name, row.score]), [[2023, '中医类', 130], [2024, '中医类', 157], [2025, '中医类', 120]])
  const sport = controlScoresForMajor(schoolFor('106'), '体育教育')
  assert.deepEqual(sport.map(row => [row.year, row.category_name]), [[2023, '体育类'], [2024, '体育类'], [2025, '教育学类']])
  assert.ok(controlScoresForMajor(schoolFor('028'), '汉语言文学').some(row => row.year === 2025 && row.score === 130))
})

test('old-only catalogs and vocational annotations never become current ordinary majors', () => {
  assert.deepEqual(activePlansForMajor(schoolFor('214'), '英语'), [])
  assert.deepEqual(controlScoresForMajor(schoolFor('214'), '英语'), [])
  assert.deepEqual(activePlansForMajor(schoolFor('006'), '财务管理'), [])
  assert.ok(schoolFor('006').plans.some(plan => plan.major_name.includes('职业本科')))
})

test('Shandong selection keys cannot collide with existing province choices', () => {
  const shandong = institutionSelectionCode({ province: 'shandong', code: '028' })
  const existing = institutionSelectionCode({ province: 'zhejiang', code: '028' })
  assert.equal(shandong, 'shandong:028')
  assert.equal(existing, '028')
  assert.notEqual(shandong, existing)
  assert.equal(institutionSelectionCode({ province: 'shanghai', code: '901' }), '901')
  assert.equal(isProvinceAvailable('shandong'), true)
  assert.equal(matchesCityPreference({ province: 'shandong', city: '济南' }, ['济南']), true)
  assert.equal(matchesCityPreference({ province: 'shandong', city: '天津' }, ['济南']), false)
  assert.equal(matchesCityPreference({ province: 'shandong', city: '天津' }, [OUTSIDE_PROVINCE_CITY]), true)
})
