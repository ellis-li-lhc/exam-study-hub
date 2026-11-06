import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {isProvinceAvailable, matchesCityPreference, OUTSIDE_PROVINCE_CITY} from './regions.js'
import {institutionSelectionCode, matchedPlansForMajor, controlScoresForMajor} from './institutionQuality.js'
import {verifiedReferenceScore} from './targetPlan.js'
const read=(code,suffix)=>JSON.parse(readFileSync(new URL(`../../../exam-study-hub-server/scraped-data/${code}-${suffix}.json`,import.meta.url)))
for(const province of ['beijing','guangxi']){
 test(`${province} opens selection, preserves provincial identity and separates control scores`,()=>{
  assert.equal(isProvinceAvailable(province),true)
  const school={province,code:'001',majorMatch:'exact',activeCatalogYear:2026,plans:read(province,'adult-programs'),controlScores:read(province,'adult-control-scores'),scores:[]}
  assert.notEqual(institutionSelectionCode(school),institutionSelectionCode({...school,province:'sichuan'}))
  assert.equal(controlScoresForMajor(school,'法学').length,2)
  assert.equal(verifiedReferenceScore(school,'法学'),null)
  assert.ok(matchedPlansForMajor(school,'消防指挥').every(p=>p.selection_eligible!==false))
 })
}
test('省份城市筛选与云南待适配状态不混淆',()=>{
 assert.equal(matchesCityPreference({province:'guangxi',city:'南宁'},['南宁']),true)
 assert.equal(matchesCityPreference({province:'beijing',city:'北京'},['北京']),true)
 assert.equal(matchesCityPreference({province:'guangxi',city:'北京'},['南宁']),false)
 assert.equal(matchesCityPreference({province:'guangxi',city:'北京'},[OUTSIDE_PROVINCE_CITY]),true)
 assert.equal(isProvinceAvailable('yunnan'),false)
})
