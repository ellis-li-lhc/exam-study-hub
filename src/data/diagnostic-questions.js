export const diagnosticQuestionBank = {
  政治: [
    {
      id: 'politics-philosophy',
      name: '马克思主义哲学基础',
      description: '物质与意识、联系与发展、实践与认识',
      questions: [
        { id: 'p1', stem: '物质的唯一特性是（ ）。', options: ['客观实在性', '可知性', '运动性', '社会历史性'], answer: 0 },
        { id: 'p2', stem: '认识的来源是（ ）。', options: ['天赋观念', '社会实践', '逻辑推演', '主观感觉'], answer: 1 },
        { id: 'p3', stem: '唯物辩证法的总特征是（ ）。', options: ['矛盾与统一', '联系和发展', '量变与质变', '否定与肯定'], answer: 1 }
      ]
    },
    {
      id: 'politics-theory',
      name: '中国特色社会主义理论',
      description: '基本路线、发展理念与现代化建设',
      questions: [
        { id: 'p4', stem: '我国社会主义初级阶段的基本路线，其核心内容通常概括为（ ）。', options: ['改革、发展、稳定', '一个中心、两个基本点', '创新、协调、绿色', '共同富裕'], answer: 1 },
        { id: 'p5', stem: '新发展理念中，引领发展的第一动力是（ ）。', options: ['协调', '开放', '创新', '共享'], answer: 2 },
        { id: 'p6', stem: '中国特色社会主义最本质的特征是（ ）。', options: ['依法治国', '人民当家作主', '中国共产党领导', '共同富裕'], answer: 2 }
      ]
    }
  ],
  英语: [
    {
      id: 'english-grammar',
      name: '基础语法',
      description: '时态、从句与非谓语动词',
      questions: [
        { id: 'e1', stem: 'She ____ in Nanjing since 2022.', options: ['lives', 'lived', 'has lived', 'is living'], answer: 2 },
        { id: 'e2', stem: 'The book ____ on the desk belongs to me.', options: ['lying', 'lies', 'lay', 'is lain'], answer: 0 },
        { id: 'e3', stem: 'This is the school ____ I studied ten years ago.', options: ['which', 'where', 'what', 'who'], answer: 1 }
      ]
    },
    {
      id: 'english-reading',
      name: '词汇与阅读',
      description: '常用词义、上下文判断与主旨理解',
      questions: [
        { id: 'e4', stem: 'The word “essential” is closest in meaning to ____.', options: ['expensive', 'necessary', 'difficult', 'popular'], answer: 1 },
        { id: 'e5', stem: '“He missed the bus; therefore, he was late.” The word “therefore” shows ____.', options: ['contrast', 'cause and result', 'example', 'time order'], answer: 1 },
        { id: 'e6', stem: 'To find the main idea of a short passage, you should first pay attention to ____.', options: ['every unfamiliar word', 'the topic sentence', 'the longest sentence', 'punctuation only'], answer: 1 }
      ]
    }
  ],
  '高等数学（二）': [
    {
      id: 'math2-function',
      name: '函数与极限',
      description: '函数性质、基本极限与连续性',
      questions: [
        { id: 'm21', stem: '函数 f(x)=1/(x-2) 的定义域是（ ）。', options: ['x>2', 'x<2', 'x≠2', '全体实数'], answer: 2 },
        { id: 'm22', stem: '当 x→0 时，sin x / x 的极限为（ ）。', options: ['0', '1', '不存在', '∞'], answer: 1 },
        { id: 'm23', stem: '若函数在某点可导，则函数在该点一定（ ）。', options: ['连续', '取得极值', '单调', '为零'], answer: 0 }
      ]
    },
    {
      id: 'math2-derivative',
      name: '导数与应用',
      description: '基本求导、单调性与极值',
      questions: [
        { id: 'm24', stem: '函数 y=x² 的导数是（ ）。', options: ['x', '2x', 'x²', '2'], answer: 1 },
        { id: 'm25', stem: '若函数在区间内导数恒大于 0，则函数在该区间（ ）。', options: ['单调递增', '单调递减', '为常数', '没有定义'], answer: 0 },
        { id: 'm26', stem: '函数 y=eˣ 的导数是（ ）。', options: ['xeˣ⁻¹', 'eˣ', '1/eˣ', 'ln x'], answer: 1 }
      ]
    }
  ],
  '高等数学（一）': [
    {
      id: 'math1-limit',
      name: '极限与连续',
      description: '基本极限、无穷小与连续判断',
      questions: [
        { id: 'm11', stem: '当 x→∞ 时，1/x 的极限是（ ）。', options: ['0', '1', '∞', '不存在'], answer: 0 },
        { id: 'm12', stem: '两个无穷小量的和通常仍是（ ）。', options: ['无穷大量', '无穷小量', '常数 1', '不确定且无法判断'], answer: 1 },
        { id: 'm13', stem: '初等函数在其定义区间内通常是（ ）。', options: ['连续的', '间断的', '不可导的', '无界的'], answer: 0 }
      ]
    },
    {
      id: 'math1-calculus',
      name: '微分与积分基础',
      description: '导数、微分和不定积分',
      questions: [
        { id: 'm14', stem: '函数 y=ln x 的导数是（ ）。', options: ['x', '1/x', 'eˣ', 'ln x'], answer: 1 },
        { id: 'm15', stem: '∫x dx 的结果是（ ）。', options: ['x+C', 'x²+C', 'x²/2+C', '1/x+C'], answer: 2 },
        { id: 'm16', stem: '函数在一点取得极值的必要条件之一通常是（ ）。', options: ['函数值为 0', '导数为 0 或不存在', '二阶导数为 0', '自变量为 0'], answer: 1 }
      ]
    }
  ],
  民法: [
    {
      id: 'civil-general',
      name: '民法总则',
      description: '民事主体、民事行为能力与代理',
      questions: [
        { id: 'c1', stem: '自然人的民事权利能力始于（ ）。', options: ['出生', '成年', '结婚', '就业'], answer: 0 },
        { id: 'c2', stem: '八周岁以上的未成年人通常属于（ ）。', options: ['完全民事行为能力人', '限制民事行为能力人', '无民事权利能力人', '法人'], answer: 1 },
        { id: 'c3', stem: '代理人在代理权限内实施行为，其法律后果通常由（ ）承担。', options: ['代理人', '被代理人', '第三人', '见证人'], answer: 1 }
      ]
    },
    {
      id: 'civil-contract',
      name: '合同与侵权基础',
      description: '合同成立、违约责任与侵权责任',
      questions: [
        { id: 'c4', stem: '当事人订立合同，可以采用书面、口头或者（ ）。', options: ['其他形式', '公证形式', '批准形式', '登记形式'], answer: 0 },
        { id: 'c5', stem: '一方不履行合同义务时，依法可能承担（ ）。', options: ['刑事责任', '违约责任', '行政处分', '道德责任'], answer: 1 },
        { id: 'c6', stem: '一般侵权责任的成立通常需要损害后果与行为之间存在（ ）。', options: ['亲属关系', '因果关系', '合同关系', '行政关系'], answer: 1 }
      ]
    }
  ],
  教育理论: [
    {
      id: 'education-basics',
      name: '教育学基础',
      description: '教育目的、教学原则与师生关系',
      questions: [
        { id: 'ed1', stem: '教育活动中最基本、最主要的关系是（ ）。', options: ['师生关系', '同事关系', '亲子关系', '邻里关系'], answer: 0 },
        { id: 'ed2', stem: '因材施教原则强调教学要关注学生的（ ）。', options: ['统一标准', '个别差异', '家庭收入', '座位位置'], answer: 1 },
        { id: 'ed3', stem: '教学过程的中心环节通常是（ ）。', options: ['备课', '上课', '考试', '布置作业'], answer: 1 }
      ]
    },
    {
      id: 'education-psychology',
      name: '教育心理学',
      description: '学习动机、记忆规律与个体差异',
      questions: [
        { id: 'ed4', stem: '直接推动学生进行学习活动的内部动力是（ ）。', options: ['学习动机', '学习成绩', '课程表', '教师年龄'], answer: 0 },
        { id: 'ed5', stem: '遗忘规律表明，复习安排通常应当（ ）。', options: ['先疏后密', '先密后疏', '只复习一次', '考前集中复习'], answer: 1 },
        { id: 'ed6', stem: '把新知识与已有知识联系起来，有助于（ ）。', options: ['机械遗忘', '意义学习', '降低动机', '消除差异'], answer: 1 }
      ]
    }
  ],
  大学语文: [
    {
      id: 'chinese-literature',
      name: '文学常识',
      description: '作家作品、文体与文学史基础',
      questions: [
        { id: 'ch1', stem: '《论语》主要记录的是（ ）。', options: ['孔子及其弟子的言行', '老子的哲学思想', '屈原的诗歌', '司马迁的史论'], answer: 0 },
        { id: 'ch2', stem: '被称为“史家之绝唱，无韵之离骚”的作品是（ ）。', options: ['《诗经》', '《史记》', '《汉书》', '《资治通鉴》'], answer: 1 },
        { id: 'ch3', stem: '唐代诗人杜甫通常被称为（ ）。', options: ['诗仙', '诗圣', '诗佛', '诗鬼'], answer: 1 }
      ]
    },
    {
      id: 'chinese-reading',
      name: '阅读与表达',
      description: '修辞、概括与文章表达方式',
      questions: [
        { id: 'ch4', stem: '“飞流直下三千尺”主要使用了（ ）修辞。', options: ['比喻', '夸张', '借代', '反问'], answer: 1 },
        { id: 'ch5', stem: '概括文章中心思想时，最应关注的是（ ）。', options: ['个别生词', '作者的核心观点与材料关系', '标点数量', '段落长短'], answer: 1 },
        { id: 'ch6', stem: '记叙文中交代人物、时间和地点，属于（ ）要素。', options: ['论证', '说明', '记叙', '抒情'], answer: 2 }
      ]
    }
  ]
}

export function getDiagnosticGroups(subjects = []) {
  return subjects.flatMap(subject => (diagnosticQuestionBank[subject] || []).map(group => ({ ...group, subject })))
}
