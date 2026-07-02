// 全国省级行政区列表（用于报考省份下拉）。
// value 用拼音码，与院校数据里的 province 字段保持一致（如 jiangsu）。
export const chinaProvinces = [
  { value: 'beijing', label: '北京' },
  { value: 'tianjin', label: '天津' },
  { value: 'hebei', label: '河北' },
  { value: 'shanxi', label: '山西' },
  { value: 'neimenggu', label: '内蒙古' },
  { value: 'liaoning', label: '辽宁' },
  { value: 'jilin', label: '吉林' },
  { value: 'heilongjiang', label: '黑龙江' },
  { value: 'shanghai', label: '上海' },
  { value: 'jiangsu', label: '江苏' },
  { value: 'zhejiang', label: '浙江' },
  { value: 'anhui', label: '安徽' },
  { value: 'fujian', label: '福建' },
  { value: 'jiangxi', label: '江西' },
  { value: 'shandong', label: '山东' },
  { value: 'henan', label: '河南' },
  { value: 'hubei', label: '湖北' },
  { value: 'hunan', label: '湖南' },
  { value: 'guangdong', label: '广东' },
  { value: 'guangxi', label: '广西' },
  { value: 'hainan', label: '海南' },
  { value: 'chongqing', label: '重庆' },
  { value: 'sichuan', label: '四川' },
  { value: 'guizhou', label: '贵州' },
  { value: 'yunnan', label: '云南' },
  { value: 'xizang', label: '西藏' },
  { value: 'shaanxi', label: '陕西' },
  { value: 'gansu', label: '甘肃' },
  { value: 'qinghai', label: '青海' },
  { value: 'ningxia', label: '宁夏' },
  { value: 'xinjiang', label: '新疆' },
  { value: 'taiwan', label: '台湾' },
  { value: 'xianggang', label: '香港' },
  { value: 'aomen', label: '澳门' }
]

// 当前已开放报考的省份（有真实招生数据）。其余省份在下拉中禁用。
export const availableProvinces = ['jiangsu', 'henan']

export const provinceCityOptions = {
  jiangsu: ['南京', '无锡', '徐州', '常州', '苏州', '南通', '连云港', '淮安', '盐城', '扬州', '镇江', '泰州', '宿迁'],
  henan: ['郑州', '开封', '洛阳', '平顶山', '安阳', '鹤壁', '新乡', '焦作', '濮阳', '许昌', '漯河', '三门峡', '南阳', '商丘', '信阳', '周口', '驻马店', '济源']
}

export function isProvinceAvailable(value) {
  return availableProvinces.includes(value)
}

export function isCityInProvince(province, city) {
  return provinceCityOptions[province]?.includes(city) || false
}
