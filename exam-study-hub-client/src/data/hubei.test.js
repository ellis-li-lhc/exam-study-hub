import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { controlScoresForMajor, institutionSelectionCode, tuitionForPlanText } from './institutionQuality.js'
import { verifiedReferenceScore } from './targetPlan.js'
import { isProvinceAvailable, matchesCityPreference, OUTSIDE_PROVINCE_CITY } from './regions.js'
const read = name => JSON.parse(readFileSync(new URL(`../../../exam-study-hub-server/scraped-data/${name}`, import.meta.url)))
const plans = read('hubei-adult-programs.json')
const controls = read('hubei-adult-control-scores.json')
test('Hubei catalogue maps to real control categories without inventing admission scores', () => {
  const school = { province:'hubei', majorMatch:'exact', activeCatalogYear:2026,
    plans:plans.filter(p=>p.institution_name==='湖北中医药大学'), controlScores:controls, scores:[], source:{confidence:'verified'} }
  const lines=controlScoresForMajor(school,'药学')
  assert.equal(lines.length,3)
  assert.ok(lines.every(r=>r.category_name==='经济管理类'))
  assert.equal(verifiedReferenceScore(school,'药学'),null)
  assert.equal(tuitionForPlanText(school.plans.find(r=>r.major_name==='药学')),'2600元/年')
  assert.ok(plans.every(p=>p.plan_count===null))
})
test('Hubei opens selection and preserves city filters and province identities', () => {
  assert.equal(isProvinceAvailable('hubei'),true)
  assert.equal(matchesCityPreference({province:'hubei',city:'武汉'},['武汉']),true)
  assert.equal(matchesCityPreference({province:'hubei',city:'西安'},[OUTSIDE_PROVINCE_CITY]),true)
  assert.notEqual(institutionSelectionCode({province:'hubei',code:'123'}),institutionSelectionCode({province:'hebei',code:'123'}))
  assert.equal(read('hubei-adult-category-collection-plans.json').length,25)
})
