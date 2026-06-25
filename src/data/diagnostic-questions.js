import englishBank from '../../docs/English.json'
import mathBank from '../../docs/Math.json'
import politicsBank from '../../docs/Politics.json'

const subjectSourceMap = {
  政治: politicsBank,
  英语: englishBank,
  '高等数学（一）': mathBank,
  '高等数学（二）': mathBank
}

const optionPrefixPattern = /^[A-D][.、．]\s*/

function normalizeOption(option) {
  return String(option).replace(optionPrefixPattern, '').trim()
}

function normalizeTopics(subject, bank) {
  return (bank?.topics || []).map((topic, topicIndex) => ({
    id: `${subject}-${topic.name}-${topicIndex}`,
    name: topic.name,
    description: `${subject} · ${topic.name} 高频知识点`,
    subject,
    questions: (topic.questions || []).map((question, questionIndex) => ({
      id: `${subject}-${topic.name}-${questionIndex}`,
      stem: question.question,
      options: (question.options || []).map(normalizeOption),
      answer: String(question.answer || '').trim().toUpperCase()
    }))
  }))
}

export const diagnosticQuestionBank = Object.fromEntries(
  Object.entries(subjectSourceMap).map(([subject, bank]) => [subject, normalizeTopics(subject, bank)])
)

export function getDiagnosticGroups(subjects = []) {
  return subjects.flatMap(subject => diagnosticQuestionBank[subject] || [])
}
