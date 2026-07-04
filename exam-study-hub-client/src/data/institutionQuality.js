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

export function latestReferenceScore(school) {
  const scores = validScores(school)
  return scores.length
    ? scores.slice().sort((a, b) => Number(b.year || 0) - Number(a.year || 0))[0]
    : null
}

export function matchedPlansForMajor(school, majorName) {
  if (!school || !majorName || school.majorMatch !== 'exact') return []
  return (school.plans || []).filter(plan => plan.major_name === majorName || plan.majorName === majorName)
}

export function institutionDataProfile(school, selectedMajor) {
  const majorName = selectedMajor?.name
  const matchedPlans = matchedPlansForMajor(school, majorName)
  const hasExactPlan = school?.majorMatch === 'exact' && (!majorName || matchedPlans.length > 0)
  const hasScore = validScores(school).length > 0
  const hasVerifiedSource = school?.source?.confidence === 'verified'
  const hasTuition = hasMeaningfulValue(school?.tuition)
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
