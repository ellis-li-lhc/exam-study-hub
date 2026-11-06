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
export const availableProvinces = ['jiangsu', 'henan', 'zhejiang', 'guangdong', 'shanghai', 'shandong', 'hebei', 'hubei', 'hunan', 'jiangxi', 'anhui', 'fujian', 'sichuan', 'chongqing', 'beijing', 'guangxi']

// 城市偏好中的特殊选项：保留在所选招生省份内招生、但校本部不在该省的院校。
export const OUTSIDE_PROVINCE_CITY = '__outside_province__'
export const OUTSIDE_PROVINCE_CITY_LABEL = '省外院校'

export const provinceCityOptions = {
  beijing: ['北京'],
  guangxi: ['南宁', '柳州', '桂林', '梧州', '北海', '防城港', '钦州', '贵港', '玉林', '百色', '贺州', '河池', '来宾', '崇左'],
  sichuan: ['成都', '自贡', '攀枝花', '泸州', '德阳', '绵阳', '广元', '遂宁', '内江', '乐山', '南充', '眉山', '宜宾', '广安', '达州', '雅安', '巴中', '资阳', '阿坝', '甘孜', '凉山'],
  chongqing: ['重庆'],
  anhui: ['合肥', '芜湖', '蚌埠', '淮南', '马鞍山', '淮北', '铜陵', '安庆', '黄山', '阜阳', '宿州', '滁州', '六安', '宣城', '池州', '亳州'],
  fujian: ['福州', '厦门', '莆田', '三明', '泉州', '漳州', '南平', '龙岩', '宁德'],
  hunan: ['长沙', '株洲', '湘潭', '衡阳', '邵阳', '岳阳', '常德', '张家界', '益阳', '郴州', '永州', '怀化', '娄底', '湘西'],
  jiangxi: ['南昌', '景德镇', '萍乡', '九江', '新余', '鹰潭', '赣州', '吉安', '宜春', '抚州', '上饶'],
  hubei: ['武汉', '黄石', '十堰', '宜昌', '襄阳', '鄂州', '荆门', '孝感', '荆州', '黄冈', '咸宁', '随州', '恩施', '仙桃', '潜江', '天门', '神农架'],
  hebei: ['石家庄', '唐山', '秦皇岛', '邯郸', '邢台', '保定', '张家口', '承德', '沧州', '廊坊', '衡水'],
  shandong: ['济南', '青岛', '淄博', '枣庄', '东营', '烟台', '潍坊', '济宁', '泰安', '威海', '日照', '临沂', '德州', '聊城', '滨州', '菏泽'],
  shanghai: ['上海'],
  jiangsu: ['南京', '无锡', '徐州', '常州', '苏州', '南通', '连云港', '淮安', '盐城', '扬州', '镇江', '泰州', '宿迁'],
  henan: ['郑州', '开封', '洛阳', '平顶山', '安阳', '鹤壁', '新乡', '焦作', '濮阳', '许昌', '漯河', '三门峡', '南阳', '商丘', '信阳', '周口', '驻马店', '济源'],
  zhejiang: ['杭州', '宁波', '温州', '嘉兴', '湖州', '绍兴', '金华', '衢州', '舟山', '台州', '丽水'],
  guangdong: ['广州', '深圳', '珠海', '汕头', '佛山', '韶关', '湛江', '肇庆', '江门', '茂名', '惠州', '梅州', '潮州', '东莞', '中山']
}

export function isProvinceAvailable(value) {
  return availableProvinces.includes(value)
}

export function isCityInProvince(province, city) {
  return provinceCityOptions[province]?.includes(city) || false
}

export function isOutsideProvinceInstitution(item) {
  return Boolean(item?.city && item.city !== '—' && !isCityInProvince(item.province, item.city))
}

export function cityPreferenceLabel(value) {
  return value === OUTSIDE_PROVINCE_CITY ? OUTSIDE_PROVINCE_CITY_LABEL : value
}

export function matchesCityPreference(item, selectedCities = []) {
  const cities = Array.isArray(selectedCities) ? selectedCities : []
  if (!cities.length) return true
  if (cities.includes(item?.city)) return true
  return cities.includes(OUTSIDE_PROVINCE_CITY) && isOutsideProvinceInstitution(item)
}
