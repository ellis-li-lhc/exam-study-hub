import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {controlScoresForMajor,matchedPlansForMajor,tuitionForMajorText,institutionSelectionCode} from './institutionQuality.js'
import {verifiedReferenceScore} from './targetPlan.js'
import {isProvinceAvailable,matchesCityPreference,OUTSIDE_PROVINCE_CITY} from './regions.js'
const read=(p,suffix)=>JSON.parse(readFileSync(new URL(`../../../exam-study-hub-server/scraped-data/${p}-${suffix}.json`,import.meta.url)))
for(const province of ['anhui','fujian']){
 test(`${province} opens province selection and preserves source school identities`,()=>{
  assert.equal(isProvinceAvailable(province),true)
  assert.equal(matchesCityPreference({province,city:province==='anhui'?'合肥':'福州'},[province==='anhui'?'合肥':'福州']),true)
  assert.equal(matchesCityPreference({province,city:'北京'},[OUTSIDE_PROVINCE_CITY]),true)
  assert.notEqual(institutionSelectionCode({province,code:'101'}),institutionSelectionCode({province:'hunan',code:'101'}))
 })
 test(`${province} uses province controls and ordinary programme details without inventing school scores`,()=>{
  const school={province,activeCatalogYear:2026,majorMatch:'exact',plans:read(province,'adult-programs'),controlScores:read(province,'adult-control-scores'),scores:[],source:{confidence:'verified'}}
  assert.equal(controlScoresForMajor(school,'法学').length,province==='anhui'?2:1)
  assert.equal(verifiedReferenceScore(school,'法学'),null)
  assert.ok(matchedPlansForMajor(school,'农学').every(p=>p.selection_eligible!==false))
 })
}
test('restricted low-fee projects cannot change ordinary tuition or teaching-site previews',()=>{
 const school={province:'fujian',activeCatalogYear:2026,majorMatch:'exact',plans:[
  {year:2026,major_name:'农学',tuition_raw:'2000元/年',teaching_site:'社会招生教学点',selection_eligible:true},
  {year:2026,major_name:'农学',tuition_raw:'1680元',teaching_site:'委培教学点',selection_eligible:false}
 ]}
 assert.equal(tuitionForMajorText(school,'农学'),'2000元/年')
 assert.equal(matchedPlansForMajor(school,'农学').length,1)
})
