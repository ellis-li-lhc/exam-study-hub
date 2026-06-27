// 诊断/阶段测试题库改为从后端获取（GET /api/questions）。
// 返回结构与原来一致：每个知识点是一个 group，含 id/name/description/subject/questions。
import { getQuestionGroups } from '../api'

export async function fetchDiagnosticGroups(subjects = []) {
  if (!subjects.length) return []
  return getQuestionGroups(subjects)
}
