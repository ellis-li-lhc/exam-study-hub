import assert from 'node:assert/strict'
import test from 'node:test'

import {
  OUTSIDE_PROVINCE_CITY,
  OUTSIDE_PROVINCE_CITY_LABEL,
  cityPreferenceLabel,
  matchesCityPreference,
} from './regions.js'

test('matchesCityPreference treats outside-province option as cross-province admission preference', () => {
  const localHenanSchool = { province: 'henan', city: '郑州' }
  const outsideHenanSchool = { province: 'henan', city: '北京' }

  assert.equal(matchesCityPreference(localHenanSchool, []), true)
  assert.equal(matchesCityPreference(localHenanSchool, ['郑州']), true)
  assert.equal(matchesCityPreference(outsideHenanSchool, ['郑州']), false)
  assert.equal(matchesCityPreference(outsideHenanSchool, [OUTSIDE_PROVINCE_CITY]), true)
  assert.equal(matchesCityPreference(outsideHenanSchool, ['郑州', OUTSIDE_PROVINCE_CITY]), true)
})

test('cityPreferenceLabel renders special outside-province preference for users', () => {
  assert.equal(cityPreferenceLabel(OUTSIDE_PROVINCE_CITY), OUTSIDE_PROVINCE_CITY_LABEL)
  assert.equal(cityPreferenceLabel('洛阳'), '洛阳')
})

test('Guangdong is available and distinguishes local from outside-province schools', () => {
  const localGuangdongSchool = { province: 'guangdong', city: '广州' }
  const outsideGuangdongSchool = { province: 'guangdong', city: '北京' }

  assert.equal(matchesCityPreference(localGuangdongSchool, ['广州']), true)
  assert.equal(matchesCityPreference(outsideGuangdongSchool, ['广州']), false)
  assert.equal(matchesCityPreference(outsideGuangdongSchool, [OUTSIDE_PROVINCE_CITY]), true)
})
