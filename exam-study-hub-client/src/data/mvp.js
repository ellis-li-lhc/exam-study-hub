// 业务常量（非演示数据）。
// 院校 / 专业 / 题库均以接口与 majors.js 为准；省份列表仅作接口失败时的最小兜底。

export const provinceOptions = [
  { value: 'henan', label: '河南', note: '户籍地，可直接按当年公告准备材料' },
  { value: 'jiangsu', label: '江苏', note: '工作地，非户籍报名需核验居住证或连续社保' },
  { value: 'zhejiang', label: '浙江', note: '已接入2025官方招生专业目录，计划人数以报名系统为准' },
  { value: 'guangdong', label: '广东', note: '已接入2025官方招生计划、第一志愿投档线及省控线' },
  { value: 'shanghai', label: '上海', note: '已接入2026专业目录、2025招生计划和征求计划；市控线独立展示，暂无院校录取线' },
  { value: 'shandong', label: '山东', note: '已接入2026及2025专业目录、2025两次征集计划；省控线独立展示，暂无院校实际录取线' },
  { value: 'anhui', label: '安徽', note: '已接入2026省级公开专升本目录71校；2024—2025省控线单列，专项限制不作为普通备考目标' },
  { value: 'fujian', label: '福建', note: '已接入2026省级公开专升本目录40校；2025省控线单列，定向及委培计划保留原文' },
  { value: 'sichuan', label: '四川', note: '已更新2026年11月第二次公布1240条专升本计划；8月目录只作历史参考，2024—2025省控线单列' },
  { value: 'chongqing', label: '重庆', note: '已接入2026市级公开专升本目录；2024—2025省控线单列，目录标注外语为英语' },
  { value: 'beijing', label: '北京', note: '已接入2026考试院专升本目录45校；2024—2025市控线单列，限定招生不作普通目标' },
  { value: 'guangxi', label: '广西', note: '已接入2026考试院专升本目录55校；2024—2025省控线单列，学费保留年费、学期及总额口径' },
  { value: 'hunan', label: '湖南', note: '已接入2026省级专升本目录；2024—2025省控线与2025两轮科类征集单列' },
  { value: 'jiangxi', label: '江西', note: '已接入14所院校2026官方资料，按专业与教学点保留；2025普通统考省控线独立展示，非全省完整目录' },
  { value: 'hubei', label: '湖北', note: '已接入5所院校2026专业简章；历年省控线与院校科类征集单列，非全省完整目录' },
  { value: 'hebei', label: '河北', note: '已接入2024—2025专升本计划，仅历史参考；未取得2026完整目录，省控线按适用人群区分' }
]

export const stageTemplates = [
  { id: 1, name: '基础建立', weeks: 4, description: '补齐核心概念，优先拿下高频基础题。', target: '基础题正确率达到 65%' },
  { id: 2, name: '专项提分', weeks: 5, description: '按薄弱知识点和题型集中训练。', target: '专项正确率达到 75%' },
  { id: 3, name: '真题训练', weeks: 4, description: '用历年真题建立答题节奏和时间感。', target: '限时完成试卷并接近目标分' },
  { id: 4, name: '模考冲刺', weeks: 3, description: '稳定成绩，减少粗心和时间分配失误。', target: '连续模考达到目标区间' }
]
