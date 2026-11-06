import test from 'node:test'
import assert from 'node:assert/strict'
import { isProvinceAvailable, matchesCityPreference, OUTSIDE_PROVINCE_CITY } from './regions.js'
import { institutionSelectionCode, matchedPlansForMajor } from './institutionQuality.js'

test('四川、重庆可选，校本部城市及跨省学校筛选正确', () => {
  for (const province of ['sichuan', 'chongqing']) assert.equal(isProvinceAvailable(province), true)
  assert.equal(matchesCityPreference({province:'sichuan',city:'阿坝'},['阿坝']),true)
  assert.equal(matchesCityPreference({province:'chongqing',city:'重庆'},['重庆']),true)
  assert.equal(matchesCityPreference({province:'chongqing',city:'成都'},['重庆']),false)
  assert.equal(matchesCityPreference({province:'chongqing',city:'成都'},[OUTSIDE_PROVINCE_CITY]),true)
})

test('相同院校在不同招生地区保持独立，单位限制不进入普通专业预览', () => {
  const school={majorMatch:'exact',province:'chongqing',code:'10635',activeCatalogYear:2026,plans:[
    {year:2026,major_name:'法学',category_name:'法学类',selection_eligible:false,tuition_amount:1000},
    {year:2026,major_name:'法学',category_name:'法学类',selection_eligible:true,tuition_amount:2800}
  ]}
  assert.notEqual(institutionSelectionCode(school),institutionSelectionCode({...school,province:'sichuan'}))
  assert.equal(matchedPlansForMajor(school,'法学').length,1)
  assert.equal(matchedPlansForMajor(school,'法学')[0].tuition_amount,2800)
})
