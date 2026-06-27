// 诊断/阶段测试题库接口
import http from './request'

// 按科目获取题库知识点分组  → GET /api/questions?subjects=政治,英语
export function getQuestionGroups(subjects) {
  return http.get('/questions', { params: { subjects: (subjects || []).join(',') } })
}
