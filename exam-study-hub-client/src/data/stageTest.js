// 阶段测试抽题：优先本阶段 focus 知识点，不足时用薄弱 backlog / 科目均分补齐；
// 软降重：优先未在诊断中答对的题。

function groupMatchesPoint(group, point) {
  if (!group || !point) return false
  if (group.subject !== point.subject) return false
  return String(group.id) === String(point.id) || group.name === point.name || group.name === point.knowledgeName
}

function flattenQuestions(group) {
  if (!group?.questions?.length) return []
  return group.questions.map(question => ({
    ...question,
    subject: group.subject,
    knowledgeName: group.name,
    groupId: group.id,
  }))
}

function pickFromGroup(group, { limit, usedQuestionIds, preferUnanswered, correctAnswerIds }) {
  const pool = flattenQuestions(group).filter(q => !usedQuestionIds.has(q.id))
  if (!pool.length || limit <= 0) return []

  const preferred = preferUnanswered
    ? pool.filter(q => !correctAnswerIds.has(q.id))
    : pool
  const ordered = preferred.length ? [...preferred, ...pool.filter(q => !preferred.includes(q))] : pool

  const picked = ordered.slice(0, limit)
  picked.forEach(q => usedQuestionIds.add(q.id))
  return picked
}

/**
 * @param {object} options
 * @param {number} options.stageId
 * @param {Array} options.focusPoints - 本阶段重点知识点
 * @param {Array} options.weaknessBacklog - 诊断薄弱 backlog（可选补齐）
 * @param {Array} options.groups - fetchDiagnosticGroups 结果
 * @param {string[]} options.subjects - 当前专业统考科目
 * @param {object} [options.diagnosticAnswers] - 诊断作答 { [questionId]: letter }
 * @param {Array} [options.answerDetails] - 诊断明细，含 correct 标记
 * @param {number} [options.limit=8]
 * @param {number} [options.perKnowledge=2]
 */
export function buildStageQuestions({
  stageId = 1,
  focusPoints = [],
  weaknessBacklog = [],
  groups = [],
  subjects = [],
  diagnosticAnswers = {},
  answerDetails = [],
  limit = 8,
  perKnowledge = 2,
} = {}) {
  const usedQuestionIds = new Set()
  const result = []
  const correctAnswerIds = new Set(
    (answerDetails || [])
      .filter(item => item.correct)
      .map(item => item.questionId || item.question_id || item.id)
      .filter(Boolean)
  )

  const findGroup = (point) => groups.find(group => groupMatchesPoint(group, point))

  // 1) 本阶段 focus 知识点
  for (const point of focusPoints) {
    if (result.length >= limit) break
    const group = findGroup(point)
    if (!group) continue
    const room = Math.min(perKnowledge, limit - result.length)
    result.push(...pickFromGroup(group, {
      limit: room,
      usedQuestionIds,
      preferUnanswered: true,
      correctAnswerIds,
    }))
  }

  // 2) 薄弱 backlog 补齐
  if (result.length < limit) {
    for (const point of weaknessBacklog) {
      if (result.length >= limit) break
      const group = findGroup(point)
      if (!group) continue
      // 已从该组抽过则跳过，避免同一知识点刷满
      if (result.some(q => q.groupId === group.id || (q.subject === group.subject && q.knowledgeName === group.name))) {
        continue
      }
      const room = Math.min(perKnowledge, limit - result.length)
      result.push(...pickFromGroup(group, {
        limit: room,
        usedQuestionIds,
        preferUnanswered: true,
        correctAnswerIds,
      }))
    }
  }

  // 3) 按科目均分补齐（不再用 groups 序号硬切）
  if (result.length < limit && subjects.length) {
    const subjectList = subjects.filter(Boolean)
    let guard = 0
    while (result.length < limit && guard < 40) {
      guard += 1
      let added = 0
      for (const subject of subjectList) {
        if (result.length >= limit) break
        const subjectGroups = groups.filter(g => g.subject === subject)
        // 轮转：阶段越高越靠后的知识点优先，避免永远只测第一组
        const offset = Math.max(0, (Number(stageId) || 1) - 1) % Math.max(subjectGroups.length, 1)
        const orderedGroups = [
          ...subjectGroups.slice(offset),
          ...subjectGroups.slice(0, offset),
        ]
        for (const group of orderedGroups) {
          if (result.length >= limit) break
          if (result.some(q => q.groupId === group.id)) continue
          const picked = pickFromGroup(group, {
            limit: 1,
            usedQuestionIds,
            preferUnanswered: true,
            correctAnswerIds,
          })
          if (picked.length) {
            result.push(...picked)
            added += picked.length
            break
          }
        }
      }
      if (!added) break
    }
  }

  // 4) 仍不足：允许重复知识点再取未用题
  if (result.length < limit) {
    for (const group of groups) {
      if (result.length >= limit) break
      result.push(...pickFromGroup(group, {
        limit: limit - result.length,
        usedQuestionIds,
        preferUnanswered: true,
        correctAnswerIds,
      }))
    }
  }

  return result.slice(0, limit)
}

/** 汇总本次测试的知识点覆盖（对/错） */
export function summarizeStageCoverage(questions = [], answers = {}) {
  const map = new Map()
  questions.forEach(question => {
    const key = `${question.subject}:${question.knowledgeName}`
    if (!map.has(key)) {
      map.set(key, {
        subject: question.subject,
        knowledgeName: question.knowledgeName,
        total: 0,
        correct: 0,
        wrong: 0,
      })
    }
    const row = map.get(key)
    row.total += 1
    if (answers[question.id] === question.answer) row.correct += 1
    else row.wrong += 1
  })
  return [...map.values()]
}

export function stageThreshold(stageId) {
  const thresholds = { 1: 65, 2: 75, 3: 75, 4: 80 }
  return thresholds[stageId] ?? 70
}
