export const provinceOptions = [
  { value: 'henan', label: '河南', note: '户籍地，可直接按当年公告准备材料' },
  { value: 'jiangsu', label: '江苏', note: '工作地，非户籍报名需核验居住证或连续社保' }
]

export const majorOptions = [
  {
    code: 'business',
    name: '工商管理',
    category: '经济管理类',
    subjects: ['政治', '英语', '高等数学（二）'],
    description: '知识结构综合，适合希望兼顾管理与职业发展的在职考生。'
  },
  {
    code: 'accounting',
    name: '会计学',
    category: '经济管理类',
    subjects: ['政治', '英语', '高等数学（二）'],
    description: '偏重财务与经营分析，专业方向清晰，就业适配面较广。'
  },
  {
    code: 'law',
    name: '法学',
    category: '法学类',
    subjects: ['政治', '英语', '民法'],
    description: '记忆与理解并重，适合对公共事务、法务方向感兴趣的考生。'
  },
  {
    code: 'education',
    name: '教育学',
    category: '教育学类',
    subjects: ['政治', '英语', '教育理论'],
    description: '以教育学和心理学基础为主，适合教育相关职业规划。'
  },
  {
    code: 'computer',
    name: '计算机科学与技术',
    category: '理工类',
    subjects: ['政治', '英语', '高等数学（一）'],
    description: '数学要求相对更高，适合已有技术经验或明确转行目标的人。'
  },
  {
    code: 'chinese',
    name: '汉语言文学',
    category: '文史中医类',
    subjects: ['政治', '英语', '大学语文'],
    description: '侧重阅读、记忆和表达，适合文字、教育及行政方向。'
  }
]

export const institutions = [
  {
    code: 'jsu-demo',
    province: 'jiangsu',
    name: '江苏示例大学',
    city: '镇江',
    majors: ['business', 'accounting', 'computer'],
    duration: '2.5 年',
    tuition: 2400,
    teachingSite: '南京 / 镇江教学点',
    degree: '课程成绩达标，通过学位外语及论文答辩',
    scores: [{ year: 2023, score: 118 }, { year: 2024, score: 125 }, { year: 2025, score: 128 }],
    sourceStatus: '待当年招生简章核验'
  },
  {
    code: 'njue-demo',
    province: 'jiangsu',
    name: '南京示例财经大学',
    city: '南京',
    majors: ['business', 'accounting', 'law'],
    duration: '2.5 年',
    tuition: 2600,
    teachingSite: '南京市教学点',
    degree: '平均成绩与学位外语达到学校当年要求',
    scores: [{ year: 2023, score: 126 }, { year: 2024, score: 132 }, { year: 2025, score: 136 }],
    sourceStatus: '待当年招生简章核验'
  },
  {
    code: 'jsnu-demo',
    province: 'jiangsu',
    name: '江苏示例师范大学',
    city: '徐州',
    majors: ['education', 'chinese'],
    duration: '2.5 年',
    tuition: 2200,
    teachingSite: '徐州市教学点',
    degree: '课程、外语和毕业论文达到学位授予要求',
    scores: [{ year: 2023, score: 132 }, { year: 2024, score: 137 }, { year: 2025, score: 140 }],
    sourceStatus: '待当年招生简章核验'
  },
  {
    code: 'henu-demo',
    province: 'henan',
    name: '河南示例大学',
    city: '开封',
    majors: ['business', 'law', 'chinese'],
    duration: '2.5 年',
    tuition: 2300,
    teachingSite: '郑州 / 开封教学点',
    degree: '专业课、学位外语与论文答辩达到要求',
    scores: [{ year: 2023, score: 122 }, { year: 2024, score: 128 }, { year: 2025, score: 131 }],
    sourceStatus: '待当年招生简章核验'
  },
  {
    code: 'hnsf-demo',
    province: 'henan',
    name: '河南示例师范大学',
    city: '新乡',
    majors: ['education', 'chinese', 'computer'],
    duration: '2.5 年',
    tuition: 2100,
    teachingSite: '新乡 / 郑州教学点',
    degree: '课程成绩合格，并满足外语和论文要求',
    scores: [{ year: 2023, score: 127 }, { year: 2024, score: 134 }, { year: 2025, score: 138 }],
    sourceStatus: '待当年招生简章核验'
  },
  {
    code: 'hncj-demo',
    province: 'henan',
    name: '河南示例财经政法大学',
    city: '郑州',
    majors: ['business', 'accounting', 'law'],
    duration: '2.5 年',
    tuition: 2500,
    teachingSite: '郑州市教学点',
    degree: '平均成绩、学位外语和毕业论文均达到要求',
    scores: [{ year: 2023, score: 130 }, { year: 2024, score: 136 }, { year: 2025, score: 142 }],
    sourceStatus: '待当年招生简章核验'
  }
]

export const stageTemplates = [
  { id: 1, name: '基础建立', weeks: 4, description: '补齐核心概念，优先拿下高频基础题。', target: '基础题正确率达到 65%' },
  { id: 2, name: '专项提分', weeks: 5, description: '按薄弱知识点和题型集中训练。', target: '专项正确率达到 75%' },
  { id: 3, name: '真题训练', weeks: 4, description: '用历年真题建立答题节奏和时间感。', target: '限时完成试卷并接近目标分' },
  { id: 4, name: '模考冲刺', weeks: 3, description: '稳定成绩，减少粗心和时间分配失误。', target: '连续模考达到目标区间' }
]

export const todayTasks = [
  { id: 1, subject: '政治', title: '马克思主义基本原理：核心概念', duration: 35, type: '知识学习', done: true },
  { id: 2, subject: '英语', title: '高频词汇 30 个 + 阅读理解 1 篇', duration: 50, type: '基础训练', done: false },
  { id: 3, subject: '高等数学（二）', title: '函数与极限基础题 12 道', duration: 60, type: '专项练习', done: false }
]
