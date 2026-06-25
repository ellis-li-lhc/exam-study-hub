import englishBank from '../../docs/English.json'
import mathOneBank from '../../docs/MathOne.json'
import mathTwoBank from '../../docs/MathTwo.json'
import politicsBank from '../../docs/Politics.json'
import chineseLiteratureBank from '../../docs/ChineseLiterature.json'
import educationTheoryBank from '../../docs/EducationTheory.json'
import civilLawBank from '../../docs/CivilLaw.json'

const subjectSourceMap = {
  政治: politicsBank,
  英语: englishBank,
  '高等数学（一）': mathOneBank,
  '高等数学（二）': mathTwoBank,
  '大学语文': chineseLiteratureBank,
  '教育理论': educationTheoryBank,
  '民法': civilLawBank
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
