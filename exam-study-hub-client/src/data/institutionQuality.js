const EMPTY_VALUES = new Set(['', '—', '-', '暂无', '暂未获取', '以院校招生简章为准', '以院校学位授予要求为准'])

export function hasMeaningfulValue(value) {
  if (value === null || value === undefined) return false
  return !EMPTY_VALUES.has(String(value).trim())
}

export function validScores(school) {
  return (school?.scores || [])
    .filter(item => item?.score !== null && item?.score !== undefined)
    .map(item => ({ ...item, score: Number(item.score) }))
    .filter(item => Number.isFinite(item.score))
}

export function normalizeInstitutionScores(scores = []) {
  return scores.map(item => ({
    ...item,
    majorCategory: item.major_category ?? item.majorCategory,
    lineType: item.line_type ?? item.lineType,
  })).sort((a, b) => Number(a.year) - Number(b.year))
}

export function scoresForMajorSelection(school, major) {
  if (school?.majorMatch === 'exact') return referenceScoresForMajor(school, major?.name)
  const scores = validScores(school)
  const tagged = scores.filter(item => item.majorCategory != null)
  return tagged.length ? tagged.filter(item => item.majorCategory === major?.category) : scores
}

export function referenceScoresForMajor(school, majorName) {
  const scores = validScores(school)
  const plans = matchedPlansForMajor(school, majorName)
  if (!plans.length) return school?.majorMatch === 'exact' && majorName ? [] : scores

  const categoryCodes = new Set(plans.map(item => String(item.category_code || item.categoryCode || '')).filter(Boolean))
  const categoryNames = new Set(plans.map(item => item.category_name || item.categoryName).filter(Boolean))
  if (!categoryCodes.size && !categoryNames.size) return scores
  const matched = scores.filter(item => {
    const scoreCode = String(item.category_code || item.categoryCode || '')
    return [...categoryCodes].some(code => scoreCode === code || scoreCode.endsWith(code))
      || categoryNames.has(item.category_name || item.categoryName)
  })
  return matched
}

export function latestReferenceScore(school, majorName) {
  const scores = referenceScoresForMajor(school, majorName)
  return scores.length
    ? scores.slice().sort((a, b) => Number(b.year || 0) - Number(a.year || 0) || b.score - a.score)[0]
    : null
}

export function verifiedFactsForMajor(school, majorName) {
  return (school?.supplementalData?.facts || []).filter(item => item.review_status === 'verified_text'
    && (item.field !== 'duration_by_major' || Object.hasOwn(item.value || {}, majorName || '')))
}

export function durationForMajor(school, majorName) {
  const planDurations = [...new Set(activePlansForMajor(school, majorName)
    .map(plan => plan.study_duration_raw).filter(hasMeaningfulValue))]
  if (planDurations.length) return planDurations.join(' / ')
  const facts = verifiedFactsForMajor(school, majorName).slice().sort((a, b) => b.year - a.year)
  for (const fact of facts) {
    if (fact.field === 'duration_by_major') return `${fact.value[majorName]} 年`
    if (fact.field === 'duration_years') return `${fact.value} 年`
    if (fact.field === 'study_years_range') return `${fact.value.minimum}–${fact.value.maximum} 年（修业年限）`
  }
  return hasMeaningfulValue(school?.duration) ? school.duration : '暂未获取'
}

export function tuitionForPlanText(plan) {
  if (plan?.tuition_raw) return plan.tuition_raw
  if (plan?.tuition_amount == null) return '暂未获取'
  if (plan.tuition_unit === 'per_academic_year') return `¥${plan.tuition_amount}/学年`
  if (plan.tuition_unit === 'total') return `总学费 ¥${plan.tuition_amount}`
  return '计费口径待核验'
}

export function matchedPlansForMajor(school, majorName) {
  if (!school || !majorName || school.majorMatch !== 'exact') return []
  return (school.plans || []).filter(plan => plan.major_name === majorName || plan.majorName === majorName)
}

export function activePlansForMajor(school, majorName) {
  const plans = matchedPlansForMajor(school, majorName)
  return school?.activeCatalogYear ? plans.filter(plan => Number(plan.year) === Number(school.activeCatalogYear)) : plans
}

export function controlScoresForMajor(school, majorName, { applicantGroup = '统考生' } = {}) {
  const categories = new Set(activePlansForMajor(school, majorName).map(plan => plan.category_name).filter(Boolean))
  const controls = (school?.controlScores || []).filter(row => school?.province !== 'hebei' || row.round === applicantGroup)
  return controls.filter(row => row.line_type === '省控线' && row.score != null && (categories.has(row.category_name)
    // Shandong lists 体育 separately in 2023/24 and within 教育学 in 2025.
    || (school?.province === 'shandong' && categories.has('体育类') && row.category_name === '教育学类'
      && !controls.some(other => other.year === row.year && other.category_name === '体育类'))))
    .sort((a, b) => Number(a.year) - Number(b.year))
}

export function institutionSelectionCode(institution) {
  // New province codes collide with existing province codes. Namespace
  // these selections while preserving all existing saved institution choices.
  return ['shandong', 'hebei'].includes(institution?.province) ? `${institution.province}:${institution.code}` : institution?.code
}

export function tuitionForMajorText(school, majorName) {
  const fees = [...new Set(activePlansForMajor(school, majorName).map(plan => plan.tuition_raw).filter(hasMeaningfulValue))]
  if (fees.length) return fees.join(' / ')
  return school?.tuition != null && Number.isFinite(Number(school.tuition)) ? `¥${school.tuition}/年` : '暂未获取'
}

export function institutionDataProfile(school, selectedMajor) {
  const majorName = selectedMajor?.name
  const matchedPlans = matchedPlansForMajor(school, majorName)
  const hasExactPlan = school?.majorMatch === 'exact' && (!majorName || matchedPlans.length > 0)
  const hasScore = scoresForMajorSelection(school, selectedMajor).length > 0
  const hasVerifiedSource = school?.source?.confidence === 'verified'
  const hasTuition = hasMeaningfulValue(school?.tuition) || activePlansForMajor(school, majorName).some(plan => hasMeaningfulValue(plan.tuition_raw))
  const hasTeachingSite = hasMeaningfulValue(school?.teachingSite)
  const hasDegree = hasMeaningfulValue(school?.degree)

  const checks = [
    { key: 'plan', label: hasExactPlan ? '专业计划' : '科类参考', ok: hasExactPlan },
    { key: 'score', label: '参考线', ok: hasScore },
    { key: 'source', label: '来源核实', ok: hasVerifiedSource },
    { key: 'tuition', label: '学费', ok: hasTuition },
    { key: 'rules', label: '教学/学位', ok: hasTeachingSite && hasDegree },
  ]
  const completed = checks.filter(item => item.ok).length

  let level = 'incomplete'
  let label = '待补充'
  let tone = 'warning'
  let summary = '关键招生信息还不完整，建议以院校招生简章再次确认。'

  if (hasExactPlan && hasScore && hasVerifiedSource) {
    level = 'verified'
    label = '高可信'
    tone = 'success'
    summary = '已匹配公开专业计划，并有公开参考线来源。'
  } else if (hasScore && hasVerifiedSource) {
    level = 'reference'
    label = '可参考'
    tone = 'info'
    summary = '有公开参考线来源，但专业层面仍按科类口径参考。'
  } else if (hasScore) {
    level = 'partial'
    label = '部分数据'
    tone = 'warning'
    summary = '有参考线，但来源或专业计划信息仍需补齐。'
  } else if (hasExactPlan && hasVerifiedSource) {
    level = 'catalog'
    label = '目录已核实'
    tone = 'info'
    summary = '已核实公开招生专业目录，暂未收录院校实际录取线。省市控线仅为最低控制线参考。'
  }

  return {
    level,
    label,
    tone,
    summary,
    completed,
    total: checks.length,
    percent: Math.round(completed / checks.length * 100),
    checks,
    matchedPlans,
  }
}
