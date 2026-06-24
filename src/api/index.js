import provinces from '../data/provinces.json'
import cities from '../data/cities.json'
import universities from '../data/universities.json'
import majors from '../data/majors.json'
import universityMajors from '../data/university-majors.json'
import historicalScores from '../data/historical-scores.json'

// 模拟 API 延迟
const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * 获取所有省份
 */
export async function getProvinces() {
  await delay()
  return provinces
}

/**
 * 根据省份代码获取城市列表
 */
export async function getCitiesByProvince(provinceCode) {
  await delay()
  return cities.filter(c => c.province === provinceCode)
}

/**
 * 根据城市代码获取大学列表
 */
export async function getUniversitiesByCity(cityCode) {
  await delay()
  return universities.filter(u => u.city === cityCode)
}

/**
 * 根据大学代码获取可报考专业列表
 */
export async function getMajorsByUniversity(universityCode) {
  await delay()
  const uniMajorLinks = universityMajors.filter(um => um.university === universityCode)
  const majorCodes = uniMajorLinks.map(um => um.major)
  return majors
    .filter(m => majorCodes.includes(m.code))
    .map(m => {
      const link = uniMajorLinks.find(um => um.major === m.code)
      return { ...m, enrollment: link?.enrollment || 0 }
    })
}

/**
 * 根据大学代码和专业代码获取往年录取分数
 */
export async function getHistoricalScores(universityCode, majorCode) {
  await delay()
  return historicalScores
    .filter(s => s.university === universityCode && s.major === majorCode)
    .sort((a, b) => b.year - a.year)
}

/**
 * 根据专业代码获取考试科目
 */
export async function getExamSubjects(majorCode) {
  await delay()
  const major = majors.find(m => m.code === majorCode)
  return major?.examSubjects || []
}

/**
 * 根据大学代码获取大学信息
 */
export async function getUniversityInfo(universityCode) {
  await delay()
  return universities.find(u => u.code === universityCode)
}

/**
 * 根据专业代码获取专业信息
 */
export async function getMajorInfo(majorCode) {
  await delay()
  return majors.find(m => m.code === majorCode)
}
