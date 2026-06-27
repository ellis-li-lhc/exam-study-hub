<template>
  <div class="schools-page page-stack">
    <section class="page-intro">
      <div><span class="section-kicker">STEP 02</span><h2>{{ store.selectedMajor?.name }}有哪些院校可报？</h2><p>{{ provinceText }} · {{ store.profile.examYear }} 年参考 · {{ store.selectedMajor?.category }}</p></div>
      <el-button @click="router.push('/profile')"><el-icon><Edit /></el-icon>修改专业</el-button>
    </section>

    <el-alert title="院校与投档线为 2025 年江苏省教育考试院数据，仅供参考；录取以当年官方招生简章为准。" type="info" show-icon :closable="false" />

    <div class="subject-strip">
      <span><el-icon><Tickets /></el-icon>统考科目</span>
      <el-tag v-for="subject in store.selectedMajor?.subjects" :key="subject" effect="plain">{{ subject }}</el-tag>
      <small>专业类别决定统考科目，院校如有加试会单独标注。</small>
    </div>

    <section class="school-layout">
      <div class="school-list">
        <article v-for="school in store.filteredInstitutions" :key="school.code" class="school-card" :class="{ selected: store.selectedInstitutionCode === school.code }" @click="store.selectInstitution(school.code)">
          <div class="school-head">
            <div class="school-avatar"><el-icon><School /></el-icon></div>
            <div class="school-name"><div><h3>{{ school.name }}</h3><el-tag v-if="store.selectedInstitutionCode === school.code" type="success" size="small">已选择</el-tag></div><p>{{ provinceName(school.province) }} · {{ school.city }} · {{ store.selectedMajor?.name }}</p></div>
            <el-radio :model-value="store.selectedInstitutionCode" :value="school.code" aria-label="选择院校" />
          </div>
          <div class="school-stats">
            <span><small>近年参考线</small><strong>{{ latestScore(school) }} 分</strong></span>
            <span><small>学制</small><strong>{{ school.duration }}</strong></span>
            <span><small>学费参考</small><strong>{{ school.tuition ? `¥${school.tuition}/年` : '暂未获取' }}</strong></span>
          </div>
          <div class="school-meta"><span><el-icon><Location /></el-icon>{{ school.teachingSite }}</span><span><el-icon><Medal /></el-icon>{{ school.degree }}</span></div>
        </article>
        <el-empty v-if="store.filteredInstitutions.length === 0" description="所选省份暂时没有该专业的演示院校" />
      </div>

      <aside class="compare-panel" v-if="selected">
        <span class="section-kicker">目标预览</span><h3>{{ selected.name }}</h3><p>{{ store.selectedMajor?.name }} · {{ selected.duration }}</p>
        <div class="score-history"><div v-for="score in selected.scores" :key="score.year"><span>{{ score.year }}</span><b>{{ score.score }}</b><i :style="{ width: `${score.score / 1.8}%` }"></i></div></div>
        <dl><div><dt>教学点</dt><dd>{{ selected.teachingSite }}</dd></div><div><dt>学位条件</dt><dd>{{ selected.degree }}</dd></div><div><dt>数据状态</dt><dd>{{ selected.sourceStatus }}</dd></div></dl>
        <el-button type="primary" size="large" class="continue-button" @click="router.push('/diagnosis')">确认目标并开始诊断<el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useApplicationStore } from '../stores/application'
const router=useRouter();const store=useApplicationStore();const selected=computed(()=>store.selectedInstitution)
const provinceText=computed(()=>store.selectedProvinces.map(item=>item.label).join('、'))
const provinceName=code=>store.provinceOptions.find(item=>item.value===code)?.label
const latestScore=school=>school.scores[school.scores.length-1]?.score
</script>

<style scoped>
.page-stack{display:flex;flex-direction:column;gap:18px}.page-intro{display:flex;align-items:flex-start;justify-content:space-between}.page-intro h2{color:var(--ink);font-size:1.7rem}.page-intro p{margin-top:5px;color:var(--text-secondary)}.section-kicker{display:block;margin-bottom:5px;color:var(--primary);font-size:.72rem;font-weight:800;letter-spacing:.1em}.subject-strip{display:flex;align-items:center;gap:9px;padding:15px 18px;border:1px solid #dbe6f5;border-radius:16px;background:#f5f9ff}.subject-strip>span{display:flex;align-items:center;gap:6px;margin-right:5px;color:var(--ink);font-weight:800;font-size:.84rem}.subject-strip small{margin-left:auto;color:var(--text-muted);font-size:.72rem}.school-layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:18px;align-items:start}.school-list{display:flex;flex-direction:column;gap:13px}.school-card{padding:20px;border:1px solid var(--line);border-radius:18px;background:#fff;cursor:pointer;transition:.2s ease}.school-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-sm)}.school-card.selected{border-color:#75a2f5;box-shadow:0 0 0 3px rgba(37,99,235,.08)}.school-head{display:flex;align-items:center;gap:13px}.school-avatar{width:44px;height:44px;display:grid;place-items:center;flex:0 0 auto;border-radius:13px;color:var(--primary);background:var(--primary-soft)}.school-name{flex:1}.school-name>div{display:flex;align-items:center;gap:8px}.school-name h3{color:var(--ink);font-size:1rem}.school-name p{color:var(--text-muted);font-size:.75rem}.school-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:17px 0;padding:14px;border-radius:13px;background:#f7f9fc}.school-stats span:not(:last-child){border-right:1px solid var(--line)}.school-stats small,.school-stats strong{display:block}.school-stats small{color:var(--text-muted);font-size:.7rem}.school-stats strong{color:var(--ink);font-size:.9rem}.school-meta{display:flex;flex-direction:column;gap:6px;color:var(--text-secondary);font-size:.74rem}.school-meta span{display:flex;align-items:center;gap:6px}.compare-panel{position:sticky;top:98px;padding:22px;border-radius:20px;color:#dce8f9;background:linear-gradient(150deg,#15243f,#24446f);box-shadow:var(--shadow-md)}.compare-panel h3{color:#fff;font-size:1.2rem}.compare-panel>p{color:#aebfd8;font-size:.8rem}.score-history{display:flex;flex-direction:column;gap:12px;margin:22px 0}.score-history>div{display:grid;grid-template-columns:40px 34px 1fr;align-items:center;gap:8px;font-size:.74rem}.score-history b{color:#fff}.score-history i{display:block;height:5px;border-radius:6px;background:#64a2ff}.compare-panel dl{display:flex;flex-direction:column;gap:12px;padding-top:16px;border-top:1px solid rgba(255,255,255,.13)}.compare-panel dt{color:#8fa8cb;font-size:.68rem}.compare-panel dd{color:#ecf3ff;font-size:.76rem}.continue-button{width:100%;margin-top:20px}.compare-panel .section-kicker{color:#78a9f8}
@media(max-width:1000px){.school-layout{grid-template-columns:1fr}.compare-panel{position:static}}@media(max-width:650px){.page-intro{gap:12px}.subject-strip{flex-wrap:wrap}.subject-strip small{width:100%;margin:4px 0 0}.school-stats{grid-template-columns:1fr}.school-stats span:not(:last-child){padding-bottom:8px;border-right:0;border-bottom:1px solid var(--line)}}
</style>

