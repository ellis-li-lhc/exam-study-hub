// 成人高考专升本常见专业 → 报考科类。
// 统考科目由科类决定；某专业是否开设、归属哪个科类，以院校当年招生计划为准。
// 投档线数据只到科类粒度，因此院校仍按科类反查；本表用于让用户按真实专业名识别和选择。

export const categorySubjects = {
  '经济管理类': ['政治', '英语', '高等数学（二）'],
  '理工类': ['政治', '英语', '高等数学（一）'],
  '法学类': ['政治', '英语', '民法'],
  '教育学类': ['政治', '英语', '教育理论'],
  '文史中医类': ['政治', '英语', '大学语文']
}

export function subjectsForCategory(category) {
  return categorySubjects[category] || []
}

export const examMajors = [
  // —— 经济管理类（统考：政治、英语、高等数学（二））——
  { code: 'gongshang-guanli', name: '工商管理', category: '经济管理类' },
  { code: 'shichang-yingxiao', name: '市场营销', category: '经济管理类' },
  { code: 'kuaiji', name: '会计学', category: '经济管理类' },
  { code: 'caiwu-guanli', name: '财务管理', category: '经济管理类' },
  { code: 'shenji', name: '审计学', category: '经济管理类' },
  { code: 'renli-ziyuan', name: '人力资源管理', category: '经济管理类' },
  { code: 'guomao', name: '国际经济与贸易', category: '经济管理类' },
  { code: 'jingjixue', name: '经济学', category: '经济管理类' },
  { code: 'jinrong', name: '金融学', category: '经济管理类' },
  { code: 'caizheng', name: '财政学', category: '经济管理类' },
  { code: 'dianzi-shangwu', name: '电子商务', category: '经济管理类' },
  { code: 'wuliu-guanli', name: '物流管理', category: '经济管理类' },
  { code: 'lvyou-guanli', name: '旅游管理', category: '经济管理类' },
  { code: 'xingzheng-guanli', name: '行政管理', category: '经济管理类' },
  { code: 'gonggong-shiye', name: '公共事业管理', category: '经济管理类' },
  { code: 'gongcheng-guanli', name: '工程管理', category: '经济管理类' },
  { code: 'fangdichan', name: '房地产开发与管理', category: '经济管理类' },
  { code: 'nonglin-jingji', name: '农林经济管理', category: '经济管理类' },

  // —— 理工类（统考：政治、英语、高等数学（一））——
  { code: 'jisuanji', name: '计算机科学与技术', category: '理工类' },
  { code: 'ruanjian', name: '软件工程', category: '理工类' },
  { code: 'wangluo-gongcheng', name: '网络工程', category: '理工类' },
  { code: 'wulianwang', name: '物联网工程', category: '理工类' },
  { code: 'dashuju', name: '数据科学与大数据技术', category: '理工类' },
  { code: 'rengong-zhineng', name: '人工智能', category: '理工类' },
  { code: 'xinxi-guanli', name: '信息管理与信息系统', category: '理工类' },
  { code: 'dianzi-xinxi', name: '电子信息工程', category: '理工类' },
  { code: 'tongxin', name: '通信工程', category: '理工类' },
  { code: 'zidonghua', name: '自动化', category: '理工类' },
  { code: 'dianqi', name: '电气工程及其自动化', category: '理工类' },
  { code: 'jixie-gongcheng', name: '机械工程', category: '理工类' },
  { code: 'jixie-zhizao', name: '机械设计制造及其自动化', category: '理工类' },
  { code: 'cheliang', name: '车辆工程', category: '理工类' },
  { code: 'tumu', name: '土木工程', category: '理工类' },
  { code: 'jianzhuxue', name: '建筑学', category: '理工类' },
  { code: 'jipaishui', name: '给排水科学与工程', category: '理工类' },
  { code: 'huagong', name: '化学工程与工艺', category: '理工类' },
  { code: 'huanjing', name: '环境工程', category: '理工类' },
  { code: 'shipin', name: '食品科学与工程', category: '理工类' },
  { code: 'cailiao', name: '材料科学与工程', category: '理工类' },
  { code: 'cehui', name: '测绘工程', category: '理工类' },
  { code: 'anquan', name: '安全工程', category: '理工类' },

  // —— 法学类（统考：政治、英语、民法）——
  { code: 'faxue', name: '法学', category: '法学类' },
  { code: 'zhishi-chanquan', name: '知识产权', category: '法学类' },
  { code: 'shehui-gongzuo', name: '社会工作', category: '法学类' },
  { code: 'jianyuxue', name: '监狱学', category: '法学类' },

  // —— 教育学类（统考：政治、英语、教育理论）——
  { code: 'jiaoyuxue', name: '教育学', category: '教育学类' },
  { code: 'xueqian', name: '学前教育', category: '教育学类' },
  { code: 'xiaoxue-jiaoyu', name: '小学教育', category: '教育学类' },
  { code: 'tiyu-jiaoyu', name: '体育教育', category: '教育学类' },
  { code: 'jiaoyu-jishu', name: '教育技术学', category: '教育学类' },
  { code: 'teshu-jiaoyu', name: '特殊教育', category: '教育学类' },
  { code: 'yingyong-xinli', name: '应用心理学', category: '教育学类' },
  { code: 'shehui-tiyu', name: '社会体育指导与管理', category: '教育学类' },

  // —— 文史中医类（统考：政治、英语、大学语文）——
  { code: 'hanyu-yanwen', name: '汉语言文学', category: '文史中医类' },
  { code: 'xinwen', name: '新闻学', category: '文史中医类' },
  { code: 'guanggao', name: '广告学', category: '文史中医类' },
  { code: 'guangbo-dianshi', name: '广播电视学', category: '文史中医类' },
  { code: 'xinmeiti', name: '网络与新媒体', category: '文史中医类' },
  { code: 'mishu', name: '秘书学', category: '文史中医类' },
  { code: 'yingyu', name: '英语', category: '文史中医类' },
  { code: 'shangwu-yingyu', name: '商务英语', category: '文史中医类' },
  { code: 'riyu', name: '日语', category: '文史中医类' },
  { code: 'lishi', name: '历史学', category: '文史中医类' },
  { code: 'zhongyi', name: '中医学', category: '文史中医类' },
  { code: 'zhongyao', name: '中药学', category: '文史中医类' },
  { code: 'zhenjiu', name: '针灸推拿学', category: '文史中医类' }
]
