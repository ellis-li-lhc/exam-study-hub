import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { examMajors } from './majors.js'
import { activePlansForMajor, controlScoresForMajor, durationForMajor, institutionDataProfile, latestReferenceScore, tuitionForMajorText, tuitionForPlanText } from './institutionQuality.js'
import { verifiedReferenceScore } from './targetPlan.js'
import { isProvinceAvailable, matchesCityPreference, OUTSIDE_PROVINCE_CITY } from './regions.js'

const read = name => JSON.parse(readFileSync(new URL(`../../../exam-study-hub-server/scraped-data/${name}`, import.meta.url)))
const plans = read('shanghai-adult-programs.json')
const controls = read('shanghai-adult-control-scores.json')
const schoolFor = code => ({
  majorMatch: 'exact', activeCatalogYear: 2026,
  plans: plans.filter(row => row.institution_code === code),
  controlScores: controls, scores: [], source: { confidence: 'verified', line_type: '招生专业目录' },
})

test('Shanghai controls never become institution scores or inferred study targets', () => {
  let checked = 0
  for (const plan of plans.filter(row => row.year === 2026)) {
    const major = examMajors.find(row => row.name === plan.major_name)
    if (!major) continue
    const school = schoolFor(plan.institution_code)
    const lines = controlScoresForMajor(school, major.name)
    assert.equal(lines.length, 3)
    assert.ok(lines.every(row => row.category_name === plan.category_name && row.line_type === '省控线'))
    assert.equal(latestReferenceScore(school, major.name), null)
    assert.equal(verifiedReferenceScore(school, major.name), null)
    assert.equal(institutionDataProfile(school, major).label, '目录已核实')
    checked++
  }
  assert.ok(checked > 100)
})

test('current plan fees and duration do not inherit an older year or another major', () => {
  const school = schoolFor('901')
  assert.equal(activePlansForMajor(school, '计算机科学与技术').length, 0)
  assert.deepEqual(controlScoresForMajor(school, '计算机科学与技术'), [])
  assert.equal(durationForMajor(school, '计算机科学与技术'), '暂未获取')
  assert.equal(tuitionForMajorText(school, '计算机科学与技术'), '暂未获取')
  assert.equal(durationForMajor(school, '护理学'), '三年')
  assert.equal(tuitionForMajorText(school, '护理学'), '4800元/学年')
  const credits = plans.filter(plan => plan.tuition_unit === 'per_credit')
  assert.equal(credits.length, 235)
  assert.ok(credits.every(plan => tuitionForPlanText(plan) === plan.tuition_raw))
})

test('Shanghai city preference separates local institutions and outside headquarters', () => {
  assert.equal(isProvinceAvailable('shanghai'), true)
  assert.equal(matchesCityPreference({ province: 'shanghai', city: '上海' }, ['上海']), true)
  assert.equal(matchesCityPreference({ province: 'shanghai', city: '北京' }, ['上海']), false)
  assert.equal(matchesCityPreference({ province: 'shanghai', city: '北京' }, [OUTSIDE_PROVINCE_CITY]), true)
})
