import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { examMajors } from './majors.js'
import { activePlansForMajor, controlScoresForMajor, institutionSelectionCode, latestReferenceScore, tuitionForPlanText } from './institutionQuality.js'
import { verifiedReferenceScore } from './targetPlan.js'
import { isProvinceAvailable, matchesCityPreference, OUTSIDE_PROVINCE_CITY } from './regions.js'

const read = name => JSON.parse(readFileSync(new URL(`../../../exam-study-hub-server/scraped-data/${name}`, import.meta.url)))
const plans = read('hebei-adult-programs.json')
const controls = read('hebei-adult-control-scores.json')
const schoolFor = code => ({ province: 'hebei', majorMatch: 'exact', activeCatalogYear: 2025,
  plans: plans.filter(row => row.institution_code === code), controlScores: controls, scores: [], source: { confidence: 'verified' } })

test('Hebei ordinary and migrant-worker controls stay separate for supported course pairs', () => {
  let checked = 0
  for (const plan of plans.filter(row => row.year === 2025)) {
    const major = examMajors.find(row => row.name === plan.major_name)
    const category = ['文史类', '中医类'].includes(plan.category_name) ? '文史中医类' : plan.category_name
    if (!major || category !== major.category) continue
    const school = schoolFor(plan.institution_code)
    const ordinary = controlScoresForMajor(school, major.name)
    const special = controlScoresForMajor(school, major.name, { applicantGroup: '农民工考生' })
    assert.equal(ordinary.length, 3)
    assert.ok(ordinary.every(row => row.round === '统考生'))
    assert.equal(special.length, 2)
    assert.ok(special.every(row => row.round === '农民工考生' && row.year >= 2024))
    assert.equal(latestReferenceScore(school, major.name), null)
    assert.equal(verifiedReferenceScore(school, major.name), null)
    checked++
  }
  assert.equal(checked, 586)
  assert.equal(controlScoresForMajor(schoolFor('142'), '汉语言文学').at(-1).score, 103)
  assert.equal(controlScoresForMajor(schoolFor('142'), '汉语言文学', { applicantGroup: '农民工考生' }).at(-1).score, 102)
})

test('Hebei historic identities and total tuition preserve source meaning', () => {
  assert.deepEqual(activePlansForMajor(schoolFor('2024-306'), '法学'), [])
  assert.notEqual(institutionSelectionCode({ province: 'hebei', code: '146' }), institutionSelectionCode({ province: 'shandong', code: '146' }))
  assert.equal(institutionSelectionCode({ province: 'jiangsu', code: '146' }), '146')
  const transport = plans.find(row => row.institution_name === '北京交通大学' && row.year === 2025)
  assert.equal(tuitionForPlanText(transport), '8000元/2.5年')
  assert.equal(transport.tuition_unit, 'total')
  assert.equal(isProvinceAvailable('hebei'), true)
  assert.equal(matchesCityPreference({ province: 'hebei', city: '石家庄' }, ['石家庄']), true)
  assert.equal(matchesCityPreference({ province: 'hebei', city: '天津' }, [OUTSIDE_PROVINCE_CITY]), true)
})
