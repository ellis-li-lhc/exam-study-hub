import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { institutions as mvpInstitutions, provinceOptions as mvpProvinces, stageTemplates, todayTasks } from '../data/mvp'
import { examMajors, subjectsForCategory } from '../data/majors'
import { getProvinces, getInstitutions } from '../api'
import { getExamDate, buildMilestones, buildDailyTasks, fmtDate } from '../data/planner'

const STORAGE_KEY = 'adult-upgrade-mvp-state'
const DIAGNOSTIC_VERSION = 'docs-json-question-bank-v1'

function getDefaultYear() {
  const now = new Date()
  return now.getMonth() + 1 <= 10 ? now.getFullYear() : now.getFullYear() + 1
}

function loadSavedState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}
  } catch {
    return {}
  }
}

function createDefaultDiagnostic() {
  return {
    version: DIAGNOSTIC_VERSION,
    completed: false,
    subjectScores: { '政治': 42, '英语': 28, '高等数学（二）': 22 },
    knowledge: 34,
    speed: 46,
    mistakeType: '基础概念不牢',
    weeklyHours: 18,
    answers: {},
    submittedSubjects: [],
    knowledgeDetails: [],
    answerDetails: [],
    correctCount: 0,
    totalQuestions: 0,
    durationSeconds: 0
  }
}

export const useApplicationStore = defineStore('application', () => {
  const saved = loadSavedState()
  const profile = ref(saved.profile || {
    provinces: [],
    cities: [],
    examYear: getDefaultYear(),
    majorCode: '',
    mode: 'plan',
    weekdayHours: 2,
    weekendHours: 4,
    startDate: new Date().toISOString().slice(0, 10)
  })
  const selectedInstitutionCode = ref(saved.selectedInstitutionCode || null)
  const diagnostic = ref(saved.diagnostic?.version === DIAGNOSTIC_VERSION ? saved.diagnostic : createDefaultDiagnostic())
  const currentStage = ref(saved.currentStage || 1)
  const tasks = ref(saved.tasks || todayTasks)
  const stageTests = ref(saved.stageTests || [])
  // 今天的任务是哪一天生成的（用于「每天自动刷新当日任务」）
  const tasksDate = ref(saved.tasksDate || null)
  // 复习队列：阶段测试沉淀的薄弱知识点，会被插入每日任务（动态纠偏）
  const reviewQueue = ref(saved.reviewQueue || [])

  // 报考专业列表（成考专升本常见专业，含所属科类）。统考科目由科类决定。
  const majorOptions = ref(examMajors)
  // 省份列表：同样本地兜底，loadProvinces() 用后端数据替换。
  const provinceOptions = ref(mvpProvinces)
  // 院校列表：本地兜底，loadInstitutions() 用后端数据替换。
  const institutions = ref(mvpInstitutions)

  // 取某院校对应「选中专业科类」的投档线，归一成 [{year, score}]。
  // 后端数据每条 score 带 majorCategory；mvp 兜底数据没有该字段，直接用。
  function relevantScores(item, category) {
    const list = item.scores || []
    const tagged = list.filter(s => s.majorCategory != null)
    if (!tagged.length) return list
    return tagged
      .filter(s => s.majorCategory === category && s.score != null)
      .map(s => ({ year: s.year, score: s.score, tuition: s.tuition }))
  }

  const selectedMajor = computed(() => {
    const major = majorOptions.value.find(item => item.code === profile.value.majorCode)
    return major ? { ...major, subjects: subjectsForCategory(major.category) } : undefined
  })
  const selectedProvinces = computed(() => provinceOptions.value.filter(item => profile.value.provinces.includes(item.value)))
  // 院校按「报考类别(科类)」反查：院校在该科类有投档线即视为可报。
  // 后端数据每条 score 带 majorCategory；本地兜底数据无该字段时回退到 majors 匹配。
  const filteredInstitutions = computed(() => {
    const category = selectedMajor.value?.category
    const cities = profile.value.cities || []
    return institutions.value
      .filter(item => {
        if (!profile.value.provinces.includes(item.province)) return false
        if (cities.length && !cities.includes(item.city)) return false
        const cats = (item.scores || []).map(s => s.majorCategory).filter(Boolean)
        if (cats.length) return cats.includes(category)
        return (item.majors || []).includes(profile.value.majorCode)
      })
      .map(item => {
        const scores = relevantScores(item, category)
        return { ...item, scores, tuition: scores[0]?.tuition ?? item.tuition }
      })
  })
  const selectedInstitution = computed(() => {
    const found = institutions.value.find(item => item.code === selectedInstitutionCode.value)
    if (!found) return undefined
    const scores = relevantScores(found, selectedMajor.value?.category)
    return { ...found, scores, tuition: scores[0]?.tuition ?? found.tuition }
  })
  const profileComplete = computed(() => profile.value.provinces.length > 0 && Boolean(profile.value.majorCode))
  const diagnosisComplete = computed(() => diagnostic.value.completed)
  const currentScore = computed(() => Object.values(diagnostic.value.subjectScores).reduce((sum, value) => sum + Number(value || 0), 0))
  const referenceScore = computed(() => {
    const scores = selectedInstitution.value?.scores || []
    return scores.length ? Math.max(...scores.map(item => item.score)) : 120
  })
  const targetScore = computed(() => referenceScore.value + 30)
  const scoreGap = computed(() => Math.max(0, targetScore.value - currentScore.value))
  const SUBJECT_MAX = 150
  // 分科目标：结合诊断结果分配，而非平均/固定权重。
  // 思路：以诊断折算分为各科起点，把“目标总分-当前总分”的增量按
  // （剩余提分空间 × 提分效率）的优先级分配；公共课提分快、专业课较慢，
  // 满分封顶后剩余增量再分给仍有空间的科目，目标之和略高于目标总分以预留波动。
  const subjectTargets = computed(() => {
    const subjects = selectedMajor.value?.subjects || []
    if (!subjects.length) return []

    const scores = diagnostic.value.subjectScores
    const details = diagnostic.value.knowledgeDetails || []
    const efficiencyByIndex = [1.25, 1, 0.75]

    const items = subjects.map((name, index) => {
      const current = Number(scores[name] || 0)
      const subjectDetails = details.filter(detail => detail.subject === name)
      const mastery = subjectDetails.length
        ? Math.round(subjectDetails.reduce((sum, detail) => sum + detail.mastery, 0) / subjectDetails.length)
        : Math.round(current / SUBJECT_MAX * 100)
      return {
        name,
        current,
        mastery,
        efficiency: efficiencyByIndex[index] ?? 0.75,
        target: current
      }
    })

    const currentTotal = items.reduce((sum, item) => sum + item.current, 0)
    const totalTarget = Math.min(SUBJECT_MAX * subjects.length, Math.round(targetScore.value * 1.05))
    let remaining = Math.max(0, totalTarget - currentTotal)

    let guard = 0
    while (remaining > 0.5 && guard < 50) {
      const open = items.filter(item => item.target < SUBJECT_MAX)
      const prioritySum = open.reduce((sum, item) => sum + (SUBJECT_MAX - item.target) * item.efficiency, 0)
      if (!open.length || prioritySum <= 0) break
      let distributed = 0
      open.forEach(item => {
        const share = remaining * ((SUBJECT_MAX - item.target) * item.efficiency / prioritySum)
        const add = Math.min(SUBJECT_MAX - item.target, share)
        item.target += add
        distributed += add
      })
      remaining -= distributed
      if (distributed < 0.5) break
      guard += 1
    }

    return items.map(item => {
      const target = Math.round(item.target)
      const points = details
        .filter(detail => detail.subject === item.name)
        .map(detail => ({ id: detail.id, name: detail.name, mastery: detail.mastery, correct: detail.correct, total: detail.total }))
        .sort((a, b) => a.mastery - b.mastery)
      return {
        name: item.name,
        current: item.current,
        mastery: item.mastery,
        target,
        gap: Math.max(0, target - item.current),
        strategy: item.mastery < 40
          ? '抓基础概念与高频送分题'
          : item.mastery < 70
            ? '针对薄弱知识点专项突破'
            : '巩固高频易错点，保持手感',
        knowledgePoints: points,
        weakPoints: points.filter(point => point.mastery < 60)
      }
    })
  })

  // 跨科目的优先复习清单：掌握度最低的若干知识点，回答“先补哪些重点”。
  const focusKnowledge = computed(() => {
    const subjects = selectedMajor.value?.subjects || []
    const details = (diagnostic.value.knowledgeDetails || []).filter(detail => subjects.includes(detail.subject))
    return [...details]
      .sort((a, b) => a.mastery - b.mastery)
      .filter(detail => detail.mastery < 60)
      .slice(0, 6)
      .map(detail => ({ id: detail.id, name: detail.name, subject: detail.subject, mastery: detail.mastery, correct: detail.correct, total: detail.total }))
  })
  const weeklyHours = computed(() => profile.value.mode === 'plan'
    ? Number(profile.value.weekdayHours) * 5 + Number(profile.value.weekendHours) * 2
    : Number(diagnostic.value.weeklyHours || 0))
  const estimatedWeeks = computed(() => Math.max(6, Math.ceil((scoreGap.value * 2.1 + 60) / Math.max(weeklyHours.value, 1))))
  const overallProgress = computed(() => Math.round(tasks.value.filter(item => item.done).length / Math.max(tasks.value.length, 1) * 100))
  const stages = computed(() => stageTemplates.map(stage => ({
    ...stage,
    status: stage.id < currentStage.value ? 'completed' : stage.id === currentStage.value ? 'active' : 'pending'
  })))

  // 参考考试日（当年 10 月第 4 个周六）与距考试天数。
  const examDate = computed(() => fmtDate(getExamDate(Number(profile.value.examYear) || getDefaultYear())))
  const daysUntilExam = computed(() => Math.max(0, Math.round((new Date(examDate.value) - new Date()) / 86400000)))

  // 达标里程碑：把四个阶段铺到 [开始日, 考试日]，给出每阶段起止日期。
  // 未来阶段从「今天」起算，所以进度落后时会自动压缩 —— 即“重排期”。
  const planMilestones = computed(() => buildMilestones(stageTemplates, {
    startDate: profile.value.startDate,
    examDate: examDate.value,
    currentStage: currentStage.value,
    today: fmtDate(new Date())
  }))

  function updateProfile(nextProfile) {
    const majorChanged = profile.value.majorCode !== nextProfile.majorCode
    profile.value = { ...profile.value, ...nextProfile }
    if (!filteredInstitutions.value.some(item => item.code === selectedInstitutionCode.value)) {
      selectedInstitutionCode.value = filteredInstitutions.value[0]?.code || null
    }
    syncDiagnosticSubjects()
    if (majorChanged) resetDiagnostic()
  }

  function selectInstitution(code) {
    selectedInstitutionCode.value = code
  }

  // 从后端加载省份列表。后端返回 {code,name,note}，映射成前端用的 {value,label,note}。
  async function loadProvinces() {
    try {
      const data = await getProvinces()
      provinceOptions.value = data.map(item => ({ value: item.code, label: item.name, note: item.note }))
    } catch (error) {
      console.warn('加载省份列表失败，已使用本地兜底数据', error)
    }
  }

  // 从后端加载院校列表，映射成前端用的形状。
  async function loadInstitutions() {
    try {
      const data = await getInstitutions()
      institutions.value = data.map(item => ({
        code: item.code,
        name: item.name,
        province: item.province,
        city: item.city || '—',
        duration: item.duration || '2.5 年',
        tuition: item.tuition ?? '—',
        teachingSite: item.teaching_site || '以院校招生简章为准',
        degree: item.degree || '以院校学位授予要求为准',
        source: item.source || null,
        sourceStatus: item.source?.confidence === 'verified'
          ? `${item.source.year} 年${item.source.provider || ''}${item.source.line_type || ''}`
          : '暂无官方数据',
        majors: item.majors || [],
        scores: (item.scores || []).map(s => ({ year: s.year, score: s.score, tuition: s.tuition, majorCategory: s.major_category })),
      }))
    } catch (error) {
      console.warn('加载院校列表失败，已使用本地兜底数据', error)
    }
  }

  function syncDiagnosticSubjects() {
    const existing = diagnostic.value.subjectScores
    diagnostic.value.subjectScores = Object.fromEntries(
      (selectedMajor.value?.subjects || []).map(subject => [subject, existing[subject] ?? 25])
    )
  }

  function completeDiagnostic(payload, completed = true) {
    diagnostic.value = { ...diagnostic.value, ...payload, version: DIAGNOSTIC_VERSION, completed }
  }

  function resetDiagnostic() {
    diagnostic.value = {
      ...createDefaultDiagnostic(),
      completed: false,
      weeklyHours: diagnostic.value.weeklyHours
    }
    syncDiagnosticSubjects()
  }

  function toggleTask(taskId) {
    const task = tasks.value.find(item => item.id === taskId)
    if (!task) return
    task.done = !task.done
    // 完成的是复习任务：从复习队列移除，避免明天再次出现。
    if (task.done && task.reviewKey) {
      reviewQueue.value = reviewQueue.value.filter(item => item.knowledgeName !== task.reviewKey)
    }
  }

  // 把薄弱知识点加入复习队列（去重）。
  function addReviews(points) {
    const existing = new Set(reviewQueue.value.map(item => item.knowledgeName))
    points.forEach(point => {
      if (point.knowledgeName && !existing.has(point.knowledgeName)) {
        reviewQueue.value.push({ subject: point.subject, knowledgeName: point.knowledgeName, addedStage: currentStage.value })
        existing.add(point.knowledgeName)
      }
    })
  }

  // 重新生成「今天」的任务（计划模式）。
  function regenerateTasks() {
    const today = fmtDate(new Date())
    tasks.value = buildDailyTasks({
      subjectTargets: subjectTargets.value,
      currentStage: currentStage.value,
      weekdayHours: profile.value.weekdayHours,
      weekendHours: profile.value.weekendHours,
      reviewQueue: reviewQueue.value,
      date: today
    })
    tasksDate.value = today
  }

  // 进入计划页时调用：跨天或任务为空则自动生成当日任务。
  function ensureTodayTasks() {
    if (profile.value.mode !== 'plan') return
    const today = fmtDate(new Date())
    if (tasksDate.value !== today || !tasks.value.length) regenerateTasks()
  }

  function submitStageTest(result) {
    const thresholds = { 1: 65, 2: 75, 3: 75, 4: 80 }
    const threshold = thresholds[currentStage.value]
    const accuracy = Number(result.accuracy || 0)
    const passed = accuracy >= threshold
    stageTests.value.push({
      stage: currentStage.value,
      ...result,
      threshold,
      passed,
      date: new Date().toISOString().slice(0, 10)
    })
    // 动态纠偏：把本次测试答错的知识点加入复习队列。
    if (Array.isArray(result.weakPoints) && result.weakPoints.length) {
      addReviews(result.weakPoints)
    }
    if (passed && currentStage.value < 4) currentStage.value += 1
    // 立即重排当日任务，让复习项 / 新阶段任务马上生效。
    if (profile.value.mode === 'plan') regenerateTasks()
    return { passed, threshold }
  }

  function advanceStage() {
    if (currentStage.value < 4) currentStage.value += 1
  }

  // —— 云端同步用 ——
  // 用云端拉取的 app_state 整块覆盖本地状态（登录后调用）。
  function hydrate(blob) {
    if (!blob || typeof blob !== 'object') return
    if (blob.profile) profile.value = blob.profile
    if ('selectedInstitutionCode' in blob) selectedInstitutionCode.value = blob.selectedInstitutionCode
    if (blob.diagnostic && blob.diagnostic.version === DIAGNOSTIC_VERSION) diagnostic.value = blob.diagnostic
    if (blob.currentStage) currentStage.value = blob.currentStage
    if (Array.isArray(blob.tasks)) tasks.value = blob.tasks
    if (Array.isArray(blob.stageTests)) stageTests.value = blob.stageTests
    if ('tasksDate' in blob) tasksDate.value = blob.tasksDate
    if (Array.isArray(blob.reviewQueue)) reviewQueue.value = blob.reviewQueue
  }

  // 退出登录时把本地状态恢复成默认值，避免下个账号看到上个账号的数据。
  function resetAll() {
    profile.value = {
      provinces: [],
      cities: [],
      examYear: getDefaultYear(),
      majorCode: '',
      mode: 'plan',
      weekdayHours: 2,
      weekendHours: 4,
      startDate: new Date().toISOString().slice(0, 10)
    }
    selectedInstitutionCode.value = null
    diagnostic.value = createDefaultDiagnostic()
    currentStage.value = 1
    tasks.value = todayTasks
    stageTests.value = []
    tasksDate.value = null
    reviewQueue.value = []
  }

  watch([profile, selectedInstitutionCode, diagnostic, currentStage, tasks, stageTests, tasksDate, reviewQueue], () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      profile: profile.value,
      selectedInstitutionCode: selectedInstitutionCode.value,
      diagnostic: diagnostic.value,
      currentStage: currentStage.value,
      tasks: tasks.value,
      stageTests: stageTests.value,
      tasksDate: tasksDate.value,
      reviewQueue: reviewQueue.value
    }))
  }, { deep: true })

  return {
    provinceOptions,
    majorOptions,
    institutions,
    profile,
    selectedInstitutionCode,
    diagnostic,
    currentStage,
    tasks,
    stageTests,
    tasksDate,
    reviewQueue,
    selectedMajor,
    selectedProvinces,
    filteredInstitutions,
    selectedInstitution,
    profileComplete,
    diagnosisComplete,
    currentScore,
    referenceScore,
    targetScore,
    scoreGap,
    subjectTargets,
    focusKnowledge,
    weeklyHours,
    estimatedWeeks,
    overallProgress,
    stages,
    examDate,
    daysUntilExam,
    planMilestones,
    updateProfile,
    selectInstitution,
    loadProvinces,
    loadInstitutions,
    completeDiagnostic,
    resetDiagnostic,
    toggleTask,
    addReviews,
    regenerateTasks,
    ensureTodayTasks,
    submitStageTest,
    advanceStage,
    hydrate,
    resetAll
  }
})
