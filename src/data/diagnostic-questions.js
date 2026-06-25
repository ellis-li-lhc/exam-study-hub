import englishBank from '../../docs/English.json'
import mathBank from '../../docs/Math.json'
import politicsBank from '../../docs/Politics.json'

const subjectSourceMap = {
  政治: politicsBank,
  英语: englishBank,
  '高等数学（一）': mathBank,
  '高等数学（二）': mathBank
}

const fallbackQuestionBank = {
  民法: [
    {
      id: 'civil-general',
      name: '民法总则',
      description: '民事主体、民事行为能力与代理',
      questions: [
        { id: 'c1', stem: '自然人的民事权利能力始于（ ）。', options: ['出生', '成年', '结婚', '就业'], answer: 'A' },
        { id: 'c2', stem: '八周岁以上的未成年人通常属于（ ）。', options: ['完全民事行为能力人', '限制民事行为能力人', '无民事权利能力人', '法人'], answer: 'B' },
        { id: 'c3', stem: '代理人在代理权限内实施行为，其法律后果通常由（ ）承担。', options: ['代理人', '被代理人', '第三人', '见证人'], answer: 'B' }
      ]
    }
  ],
  教育理论: [
    {
      id: 'education-basics',
      name: '教育学基础',
      description: '教育目的、教学原则与师生关系',
      questions: [
        { id: 'ed1', stem: '教育活动中最基本、最主要的关系是（ ）。', options: ['师生关系', '同事关系', '亲子关系', '邻里关系'], answer: 'A' },
        { id: 'ed2', stem: '因材施教原则强调教学要关注学生的（ ）。', options: ['统一标准', '个别差异', '家庭收入', '座位位置'], answer: 'B' },
        { id: 'ed3', stem: '教学过程的中心环节通常是（ ）。', options: ['备课', '上课', '考试', '布置作业'], answer: 'B' }
      ]
    }
  ],
  大学语文: [
    {
      id: 'chinese-literature',
      name: '文学常识',
      description: '作家作品、文体与文学史基础',
      questions: [
        { id: 'ch1', stem: '《论语》主要记录的是（ ）。', options: ['孔子及其弟子的言行', '老子的哲学思想', '屈原的诗歌', '司马迁的史论'], answer: 'A' },
        { id: 'ch2', stem: '被称为“史家之绝唱，无韵之离骚”的作品是（ ）。', options: ['《诗经》', '《史记》', '《汉书》', '《资治通鉴》'], answer: 'B' },
        { id: 'ch3', stem: '唐代诗人杜甫通常被称为（ ）。', options: ['诗仙', '诗圣', '诗佛', '诗鬼'], answer: 'B' }
      ]
    }
  ]
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
  return subjects.flatMap(subject => diagnosticQuestionBank[subject] || fallbackQuestionBank[subject] || [])
}
