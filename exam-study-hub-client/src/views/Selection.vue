<template>
  <div class="profile-page page-stack">
    <section class="page-intro">
      <div><span class="section-kicker">STEP 01</span><h2>建立我的报考档案</h2><p>只保留真正影响择专业、匹配科目和排学习计划的信息。</p></div>
      <el-tag type="success" effect="plain">约 2 分钟</el-tag>
    </section>

    <el-form label-position="top" class="profile-form" @submit.prevent>
      <el-card shadow="never" class="form-card">
        <template #header><div class="form-heading"><span>1</span><div><h3>我可以在哪报名？</h3><p>支持多选。目前江苏、河南已接入公开招生数据，其余省份陆续接入。</p></div></div></template>
        <el-select v-model="draft.provinces" multiple filterable size="large" placeholder="选择报考省份" class="province-select">
          <el-option v-for="province in chinaProvinces" :key="province.value" :label="province.label" :value="province.value" :disabled="!isProvinceAvailable(province.value)">
            <span>{{ province.label }}</span>
            <span v-if="!isProvinceAvailable(province.value)" class="option-tag">暂未开放</span>
          </el-option>
        </el-select>
        <el-alert class="policy-tip" type="info" show-icon :closable="false" title="户籍地通常可直接报名；非户籍地可能需要居住证或连续 3～6 个月社保，最终以当年省级公告为准。" />
        <div v-if="cityOptions.length" class="city-block">
          <label class="city-label">院校所在地偏好（可选，可多选）</label>
          <el-select v-model="draft.cities" multiple clearable filterable size="large" placeholder="不限所在地，包含省内与省外招生院校" class="city-select">
            <el-option v-for="option in cityOptions" :key="option.value" :label="option.label" :value="option.value">
              <span>{{ option.label }}</span>
              <span v-if="option.note" class="option-tag">{{ option.note }}</span>
            </el-option>
          </el-select>
          <p class="city-help">选择具体城市会按校本部所在地筛选；如也接受在所选省份招生的外省学校，请勾选“省外院校”。</p>
        </div>
      </el-card>

      <el-card shadow="never" class="form-card">
        <template #header><div class="form-heading"><span>2</span><div><h3>参考哪个考试年度？</h3><p>1～10 月默认当年，11～12 月默认下一年，仍可手动修改。</p></div></div></template>
        <div class="year-row">
          <el-select v-model="draft.examYear" filterable size="large" aria-label="参考考试年度">
            <el-option v-for="year in yearOptions" :key="year" :label="`${year} 年成人高考`" :value="year" />
          </el-select>
          <div class="year-note"><el-icon><Calendar /></el-icon><span>当前按 {{ draft.examYear }} 年考试周期规划，10 月后自动切换下一年度。</span></div>
        </div>
      </el-card>

      <el-card shadow="never" class="form-card">
        <template #header><div class="form-heading"><span>3</span><div><h3>我想报什么专业？</h3><p>搜索或选择你的专业，系统据此匹配报考科类与统考科目。</p></div></div></template>
        <el-select v-model="draft.majorCode" filterable placeholder="输入关键词搜索，或下拉选择专业" size="large" class="major-select">
          <el-option-group v-for="group in majorGroups" :key="group.category" :label="group.category">
            <el-option v-for="major in group.majors" :key="major.code" :label="major.name" :value="major.code" />
          </el-option-group>
        </el-select>
        <div v-if="selectedDraftMajor" class="major-detail">
          <el-tag type="info" effect="plain">{{ selectedDraftMajor.category }}</el-tag>
          <span>统考科目：{{ subjectsForCategory(selectedDraftMajor.category).join('、') }}</span>
        </div>
        <el-alert class="policy-tip" type="info" show-icon :closable="false" title="专业按常见成考专升本目录列出；某专业是否开设、所属科类与统考科目，以院校当年招生计划为准。" />
      </el-card>

      <el-card shadow="never" class="form-card">
        <template #header><div class="form-heading"><span>4</span><div><h3>我希望怎么学？</h3><p>两种模式共享阶段路线和测试，只在每日排程方式上不同。</p></div></div></template>
        <el-radio-group v-model="draft.mode" class="mode-grid">
          <el-radio value="plan" border><span class="mode-title"><el-icon><Calendar /></el-icon>计划模式</span><small>给出可用时间，系统自动安排每日任务。</small></el-radio>
          <el-radio value="self" border><span class="mode-title"><el-icon><Compass /></el-icon>自主模式</span><small>保留阶段目标与测试，每天学什么由自己决定。</small></el-radio>
        </el-radio-group>
        <div v-if="draft.mode === 'plan'" class="time-settings">
          <el-form-item label="工作日每天"><el-input-number v-model="draft.weekdayHours" :min="0.5" :max="8" :step="0.5" /><span>小时</span></el-form-item>
          <el-form-item label="周末每天"><el-input-number v-model="draft.weekendHours" :min="0.5" :max="12" :step="0.5" /><span>小时</span></el-form-item>
          <el-form-item label="计划开始日期"><el-date-picker v-model="draft.startDate" type="date" value-format="YYYY-MM-DD" /></el-form-item>
          <div class="weekly-total"><small>预计每周投入</small><strong>{{ weeklyTotal }} 小时</strong></div>
        </div>
      </el-card>

      <div class="form-actions"><span>档案已绑定到你的账号，登录后在任意设备自动同步。</span><el-button type="primary" size="large" :disabled="!canSave" @click="saveAndContinue">保存并查看院校<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button></div>
    </el-form>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useApplicationStore } from '../stores/application'
import {
  OUTSIDE_PROVINCE_CITY,
  OUTSIDE_PROVINCE_CITY_LABEL,
  chinaProvinces,
  isCityInProvince,
  isOutsideProvinceInstitution,
  isProvinceAvailable,
} from '../data/regions'
import { subjectsForCategory } from '../data/majors'

const router = useRouter(); const store = useApplicationStore(); const currentYear = new Date().getFullYear()
const draft = reactive(JSON.parse(JSON.stringify(store.profile)))
if (!Array.isArray(draft.cities)) draft.cities = []
const yearOptions = [currentYear, currentYear + 1, currentYear + 2]
const weeklyTotal = computed(() => Number(draft.weekdayHours) * 5 + Number(draft.weekendHours) * 2)
const canSave = computed(() => draft.provinces.length > 0 && draft.majorCode && draft.mode)
// 院校所在地偏好：展示所选招生省份内的本省城市；如存在跨省招生院校，追加“省外院校”选项。
const cityOptions = computed(() => {
  const set = new Set()
  let hasOutside = false
  store.institutions.forEach(item => {
    if (!draft.provinces.includes(item.province) || !item.city || item.city === '—') return
    if (isCityInProvince(item.province, item.city)) {
      set.add(item.city)
    } else if (isOutsideProvinceInstitution(item)) {
      hasOutside = true
    }
  })
  const options = [...set]
    .sort((a, b) => a.localeCompare(b, 'zh'))
    .map(city => ({ label: city, value: city }))
  if (hasOutside) {
    options.push({ label: OUTSIDE_PROVINCE_CITY_LABEL, value: OUTSIDE_PROVINCE_CITY, note: '跨省招生' })
  }
  return options
})
const cityOptionValues = computed(() => cityOptions.value.map(option => option.value))
// 省份变化时，剔除已不在可选范围内的所在地偏好
watch(() => draft.provinces.slice(), () => {
  draft.cities = draft.cities.filter(city => cityOptionValues.value.includes(city))
})
// 专业按科类分组展示
const CATEGORY_ORDER = ['经济管理类', '理工类', '法学类', '教育学类', '文史中医类']
const majorGroups = computed(() => CATEGORY_ORDER
  .map(category => ({ category, majors: store.majorOptions.filter(item => item.category === category) }))
  .filter(group => group.majors.length))
const selectedDraftMajor = computed(() => store.majorOptions.find(item => item.code === draft.majorCode))
function saveAndContinue(){ store.updateProfile(draft); router.push('/schools') }
</script>

<style scoped lang="less" src="../styles/views/Selection.less"></style>
