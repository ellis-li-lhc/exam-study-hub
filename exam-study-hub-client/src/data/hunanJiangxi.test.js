import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { controlScoresForMajor, institutionSelectionCode, tuitionForPlanText } from './institutionQuality.js'
import { verifiedReferenceScore } from './targetPlan.js'
import { isProvinceAvailable, matchesCityPreference, OUTSIDE_PROVINCE_CITY } from './regions.js'
const read = name => JSON.parse(readFileSync(new URL(`../../../exam-study-hub-server/scraped-data/${name}`, import.meta.url)))
for (const province of ['hunan','jiangxi']) {
  test(`${province} supports selection and keeps province identities separate`, () => {
    assert.equal(isProvinceAvailable(province), true)
    assert.notEqual(institutionSelectionCode({province,code:'10543'}), institutionSelectionCode({province:'hebei',code:'10543'}))
    assert.equal(matchesCityPreference({province,city:province==='hunan'?'长沙':'南昌'},[province==='hunan'?'长沙':'南昌']),true)
    assert.equal(matchesCityPreference({province,city:'北京'},[OUTSIDE_PROVINCE_CITY]),true)
  })
  test(`${province} uses category control lines without inventing institution admission scores`, () => {
    const plans=read(`${province}-adult-programs.json`)
    const school={province,activeCatalogYear:2026,majorMatch:'exact',plans,controlScores:read(`${province}-adult-control-scores.json`),scores:[],source:{confidence:'verified'}}
    const controls=controlScoresForMajor(school,'法学')
    assert.equal(controls.length,province==='hunan'?2:1)
    assert.ok(controls.every(r=>r.category_name==='法学类'))
    assert.equal(verifiedReferenceScore(school,'法学'),null)
    assert.ok(plans.every(r=>r.plan_count===null))
    if (province==='jiangxi') {
      const psychology=plans.find(r=>r.major_name==='心理学')
      assert.equal(psychology.category_name,'经济管理类')
      assert.equal(tuitionForPlanText(psychology),'1700元/学年')
    }
  })
}
