// 业务常量（非演示数据）。
// 院校 / 专业 / 题库均以接口与 majors.js 为准；省份列表仅作接口失败时的最小兜底。

export const provinceOptions = [
  { value: 'henan', label: '河南', note: '户籍地，可直接按当年公告准备材料' },
  { value: 'jiangsu', label: '江苏', note: '工作地，非户籍报名需核验居住证或连续社保' },
  { value: 'zhejiang', label: '浙江', note: '已接入2025官方招生专业目录，计划人数以报名系统为准' }
]

export const stageTemplates = [
  { id: 1, name: '基础建立', weeks: 4, description: '补齐核心概念，优先拿下高频基础题。', target: '基础题正确率达到 65%' },
  { id: 2, name: '专项提分', weeks: 5, description: '按薄弱知识点和题型集中训练。', target: '专项正确率达到 75%' },
  { id: 3, name: '真题训练', weeks: 4, description: '用历年真题建立答题节奏和时间感。', target: '限时完成试卷并接近目标分' },
  { id: 4, name: '模考冲刺', weeks: 3, description: '稳定成绩，减少粗心和时间分配失误。', target: '连续模考达到目标区间' }
]
