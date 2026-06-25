<template>
  <div class="profile-page page-stack">
    <section class="page-intro">
      <div><span class="section-kicker">STEP 01</span><h2>建立我的报考档案</h2><p>只保留真正影响择专业、匹配科目和排学习计划的信息。</p></div>
      <el-tag type="success" effect="plain">约 2 分钟</el-tag>
    </section>

    <el-form label-position="top" class="profile-form" @submit.prevent>
      <el-card shadow="never" class="form-card">
        <template #header><div class="form-heading"><span>1</span><div><h3>我可以在哪报名？</h3><p>支持多选，你可以同时比较河南与江苏的招生院校。</p></div></div></template>
        <el-checkbox-group v-model="draft.provinces" class="choice-grid province-grid">
          <el-checkbox v-for="province in store.provinceOptions" :key="province.value" :value="province.value" border>
            <strong>{{ province.label }}</strong><small>{{ province.note }}</small>
          </el-checkbox>
        </el-checkbox-group>
        <el-alert class="policy-tip" type="info" show-icon :closable="false" title="户籍地通常可直接报名；非户籍地可能需要居住证或连续 3～6 个月社保，最终以当年省级公告为准。" />
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
        <template #header><div class="form-heading"><span>3</span><div><h3>我想报什么专业？</h3><p>专业决定考试类别与科目，确认后再反查招生院校。</p></div></div></template>
        <el-radio-group v-model="draft.majorCode" class="major-grid">
          <el-radio v-for="major in store.majorOptions" :key="major.code" :value="major.code" border>
            <span class="major-name">{{ major.name }}</span><el-tag size="small" type="info">{{ major.category }}</el-tag>
            <small>{{ major.description }}</small><b>科目：{{ major.subjects.join('、') }}</b>
          </el-radio>
        </el-radio-group>
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

      <div class="form-actions"><span>档案保存在本机浏览器，接入后端后再同步到数据库。</span><el-button type="primary" size="large" :disabled="!canSave" @click="saveAndContinue">保存并查看院校<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button></div>
    </el-form>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useApplicationStore } from '../stores/application'

const router = useRouter(); const store = useApplicationStore(); const currentYear = new Date().getFullYear()
const draft = reactive(JSON.parse(JSON.stringify(store.profile)))
const yearOptions = [currentYear, currentYear + 1, currentYear + 2]
const weeklyTotal = computed(() => Number(draft.weekdayHours) * 5 + Number(draft.weekendHours) * 2)
const canSave = computed(() => draft.provinces.length > 0 && draft.majorCode && draft.mode)
function saveAndContinue(){ store.updateProfile(draft); router.push('/schools') }
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}.page-intro{display:flex;align-items:flex-start;justify-content:space-between}.page-intro h2{color:var(--ink);font-size:1.7rem}.page-intro p{margin-top:5px;color:var(--text-secondary)}.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}.profile-form{display:flex;flex-direction:column;gap:16px}.form-card{border-radius:20px;border-color:var(--line)}.form-heading{display:flex;gap:13px;align-items:center}.form-heading>span{width:32px;height:32px;display:grid;place-items:center;border-radius:10px;color:var(--primary);font-weight:800;background:var(--primary-soft)}.form-heading h3{color:var(--ink);font-size:1rem}.form-heading p{color:var(--text-muted);font-size:.76rem}.choice-grid,.major-grid,.mode-grid{display:grid;width:100%;gap:12px}.province-grid,.mode-grid{grid-template-columns:repeat(2,1fr)}.major-grid{grid-template-columns:repeat(3,1fr)}
:deep(.el-checkbox.is-bordered),:deep(.el-radio.is-bordered){width:100%;height:auto;margin:0;padding:16px;border-radius:14px;align-items:flex-start}:deep(.el-checkbox__label),:deep(.el-radio__label){width:100%;white-space:normal}:deep(.el-checkbox__label strong),:deep(.el-checkbox__label small){display:block}:deep(.el-checkbox__label small){margin-top:4px;color:var(--text-secondary);font-size:.75rem}.policy-tip{margin-top:14px}.year-row{display:flex;align-items:center;gap:18px}.year-row .el-select{width:240px}.year-note{display:flex;align-items:center;gap:8px;color:var(--text-secondary);font-size:.8rem}.major-name{font-weight:800;color:var(--ink);margin-right:8px}.major-grid small,.major-grid b{display:block}.major-grid small{min-height:42px;margin:8px 0;color:var(--text-secondary);font-size:.74rem}.major-grid b{color:var(--primary-deep);font-size:.72rem}.mode-title{display:flex;align-items:center;gap:7px;color:var(--ink);font-weight:800}.mode-grid small{display:block;margin-top:7px;color:var(--text-secondary);font-size:.76rem}.time-settings{display:grid;grid-template-columns:repeat(4,1fr);align-items:end;gap:16px;margin-top:18px;padding:18px;border-radius:14px;background:#f7f9fd}.time-settings .el-form-item{margin:0}.time-settings .el-form-item span{margin-left:7px;color:var(--text-muted)}.weekly-total small,.weekly-total strong{display:block}.weekly-total small{color:var(--text-muted);font-size:.74rem}.weekly-total strong{color:var(--primary);font-size:1.35rem}.form-actions{display:flex;align-items:center;justify-content:space-between;padding:8px 2px}.form-actions>span{color:var(--text-muted);font-size:.76rem}
@media(max-width:1000px){.major-grid{grid-template-columns:repeat(2,1fr)}.time-settings{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.province-grid,.mode-grid,.major-grid,.time-settings{grid-template-columns:1fr}.year-row,.form-actions{align-items:stretch;flex-direction:column}.year-row .el-select{width:100%}}
</style>

