<template>
  <div class="profile-page page-stack">
    <section class="page-intro">
      <div><span class="section-kicker">STEP 01</span><h2>建立我的报考档案</h2><p>只保留真正影响择专业、匹配科目和排学习计划的信息。</p></div>
      <el-tag type="success" effect="plain">约 2 分钟</el-tag>
    </section>

    <el-form label-position="top" class="profile-form" @submit.prevent>
      <el-card shadow="never" class="form-card">
        <template #header><div class="form-heading"><span>1</span><div><h3>我可以在哪报名？</h3><p>支持多选。目前江苏、河南已接入公开招生数据，其余省份陆续接入。</p></div></div></template>
        <el-select v-model="draft.provinces" multiple size="large" placeholder="选择报考省份" class="province-select">
          <el-option v-for="province in chinaProvinces" :key="province.value" :label="province.label" :value="province.value" :disabled="!isProvinceAvailable(province.value)">
            <span>{{ province.label }}</span>
            <span v-if="!isProvinceAvailable(province.value)" class="option-tag">暂未开放</span>
          </el-option>
        </el-select>
        <el-alert class="policy-tip" type="info" show-icon :closable="false" title="户籍地通常可直接报名；非户籍地可能需要居住证或连续 3～6 个月社保，最终以当年省级公告为准。" />
        <div v-if="cityOptions.length" class="city-block">
          <label class="city-label">意向城市（可选，可多选）</label>
          <el-select v-model="draft.cities" multiple clearable size="large" placeholder="不限城市，按省内城市筛选院校" class="city-select">
            <el-option v-for="city in cityOptions" :key="city" :label="city" :value="city" />
          </el-select>
        </div>
      </el-card>

      <el-card shadow="never" class="form-card">
        <template #header><div class="form-heading"><span>2</span><div><h3>参考哪个考试年度？</h3><p>1～10 月默认当年，11～12 月默认下一年，仍可手动修改。</p></div></div></template>
        <div class="year-row">
          <el-select v-model="draft.examYear" size="large" aria-label="参考考试年度">
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
import { chinaProvinces, isCityInProvince, isProvinceAvailable } from '../data/regions'
import { subjectsForCategory } from '../data/majors'

const router = useRouter(); const store = useApplicationStore(); const currentYear = new Date().getFullYear()
const draft = reactive(JSON.parse(JSON.stringify(store.profile)))
if (!Array.isArray(draft.cities)) draft.cities = []
const yearOptions = [currentYear, currentYear + 1, currentYear + 2]
const weeklyTotal = computed(() => Number(draft.weekdayHours) * 5 + Number(draft.weekendHours) * 2)
const canSave = computed(() => draft.provinces.length > 0 && draft.majorCode && draft.mode)
// 意向城市：只展示所选省份内、且当前数据里有院校的城市；外省高校的校本部城市不进入这里。
const cityOptions = computed(() => {
  const set = new Set()
  store.institutions.forEach(item => {
    if (
      draft.provinces.includes(item.province) &&
      item.city &&
      item.city !== '—' &&
      isCityInProvince(item.province, item.city)
    ) {
      set.add(item.city)
    }
  })
  return [...set].sort((a, b) => a.localeCompare(b, 'zh'))
})
// 省份变化时，剔除已不在可选范围内的城市
watch(() => draft.provinces.slice(), () => {
  draft.cities = draft.cities.filter(city => cityOptions.value.includes(city))
})
// 专业按科类分组展示
const CATEGORY_ORDER = ['经济管理类', '理工类', '法学类', '教育学类', '文史中医类']
const majorGroups = computed(() => CATEGORY_ORDER
  .map(category => ({ category, majors: store.majorOptions.filter(item => item.category === category) }))
  .filter(group => group.majors.length))
const selectedDraftMajor = computed(() => store.majorOptions.find(item => item.code === draft.majorCode))
function saveAndContinue(){ store.updateProfile(draft); router.push('/schools') }
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}.page-intro{display:flex;align-items:flex-start;justify-content:space-between}.page-intro h2{color:var(--ink);font-size:1.7rem}.page-intro p{margin-top:5px;color:var(--text-secondary)}.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}.profile-form{display:flex;flex-direction:column;gap:16px}.form-card{border-radius:20px;border-color:var(--line)}.form-heading{display:flex;gap:13px;align-items:center}.form-heading>span{width:32px;height:32px;display:grid;place-items:center;border-radius:10px;color:var(--primary);font-weight:800;background:var(--primary-soft)}.form-heading h3{color:var(--ink);font-size:1rem}.form-heading p{color:var(--text-muted);font-size:.76rem}.choice-grid,.major-grid,.mode-grid{display:grid;width:100%;gap:12px}.province-grid,.mode-grid{grid-template-columns:repeat(2,1fr)}.major-grid{grid-template-columns:repeat(3,1fr)}
:deep(.el-checkbox.is-bordered),:deep(.el-radio.is-bordered){width:100%;height:auto;margin:0;padding:16px;border-radius:14px;align-items:flex-start}:deep(.el-checkbox__label),:deep(.el-radio__label){width:100%;white-space:normal}:deep(.el-checkbox__label strong),:deep(.el-checkbox__label small){display:block}:deep(.el-checkbox__label small){margin-top:4px;color:var(--text-secondary);font-size:.75rem}.policy-tip{margin-top:14px}.province-select{width:100%;max-width:420px}.option-tag{float:right;color:var(--text-muted);font-size:.72rem}.major-select{width:100%;max-width:420px}.major-detail{display:flex;align-items:center;gap:10px;margin-top:12px;color:var(--text-secondary);font-size:.82rem}.city-block{margin-top:16px}.city-label{display:block;margin-bottom:8px;color:var(--text-secondary);font-size:.82rem;font-weight:600}.city-select{width:100%;max-width:420px}.year-row{display:flex;align-items:center;gap:18px}.year-row .el-select{width:240px}.year-note{display:flex;align-items:center;gap:8px;color:var(--text-secondary);font-size:.8rem}.major-name{font-weight:800;color:var(--ink);margin-right:8px}.major-grid small,.major-grid b{display:block}.major-grid small{min-height:42px;margin:8px 0;color:var(--text-secondary);font-size:.74rem}.major-grid b{color:var(--primary-deep);font-size:.72rem}.mode-title{display:flex;align-items:center;gap:7px;color:var(--ink);font-weight:800}.mode-grid small{display:block;margin-top:7px;color:var(--text-secondary);font-size:.76rem}.time-settings{display:grid;grid-template-columns:repeat(4,1fr);align-items:end;gap:16px;margin-top:18px;padding:18px;border-radius:14px;background:#f7f9fd}.time-settings .el-form-item{margin:0}.time-settings .el-form-item span{margin-left:7px;color:var(--text-muted)}.weekly-total small,.weekly-total strong{display:block}.weekly-total small{color:var(--text-muted);font-size:.74rem}.weekly-total strong{color:var(--primary);font-size:1.35rem}.form-actions{display:flex;align-items:center;justify-content:space-between;padding:8px 2px}.form-actions>span{color:var(--text-muted);font-size:.76rem}
@media(max-width:1000px){.major-grid{grid-template-columns:repeat(2,1fr)}.time-settings{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.province-grid,.mode-grid,.major-grid,.time-settings{grid-template-columns:1fr}.year-row,.form-actions{align-items:stretch;flex-direction:column}.year-row .el-select{width:100%}}
</style>
