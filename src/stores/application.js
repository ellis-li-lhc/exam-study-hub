import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { institutions, majorOptions, provinceOptions, stageTemplates, todayTasks } from '../data/mvp'

const STORAGE_KEY = 'adult-upgrade-mvp-state'

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

export const useApplicationStore = defineStore('application', () => {
  const saved = loadSavedState()
  const profile = ref(saved.profile || {
    provinces: ['henan', 'jiangsu'],
    examYear: getDefaultYear(),
    majorCode: 'business',
    mode: 'plan',
    weekdayHours: 2,
    weekendHours: 4,
    startDate: new Date().toISOString().slice(0, 10)
  })
  const selectedInstitutionCode = ref(saved.selectedInstitutionCode || 'njue-demo')
  const diagnostic = ref(saved.diagnostic || {
    completed: false,
    subjectScores: { '政治': 42, '英语': 28, '高等数学（二）': 22 },
    knowledge: 34,
    speed: 46,
    mistakeType: '基础概念不牢',
    weeklyHours: 18,
    answers: {},
    knowledgeDetails: [],
    correctCount: 0,
    totalQuestions: 0,
    durationSeconds: 0
  })
  const currentStage = ref(saved.currentStage || 1)
  const tasks = ref(saved.tasks || todayTasks)
  const stageTests = ref(saved.stageTests || [])

  const selectedMajor = computed(() => majorOptions.find(item => item.code === profile.value.majorCode))
  const selectedProvinces = computed(() => provinceOptions.filter(item => profile.value.provinces.includes(item.value)))
  const filteredInstitutions = computed(() => institutions.filter(item => (
    profile.value.provinces.includes(item.province) && item.majors.includes(profile.value.majorCode)
  )))
  const selectedInstitution = computed(() => institutions.find(item => item.code === selectedInstitutionCode.value))
  const profileComplete = computed(() => profile.value.provinces.length > 0 && Boolean(profile.value.majorCode))
  const diagnosisComplete = computed(() => diagnostic.value.completed)
  const currentScore = computed(() => Object.values(diagnostic.value.subjectScores).reduce((sum, value) => sum + Number(value || 0), 0))
  const referenceScore = computed(() => {
    const scores = selectedInstitution.value?.scores || []
    return scores.length ? Math.max(...scores.map(item => item.score)) : 120
  })
  const targetScore = computed(() => referenceScore.value + 30)
  const scoreGap = computed(() => Math.max(0, targetScore.value - currentScore.value))
  const weeklyHours = computed(() => profile.value.mode === 'plan'
    ? Number(profile.value.weekdayHours) * 5 + Number(profile.value.weekendHours) * 2
    : Number(diagnostic.value.weeklyHours || 0))
  const estimatedWeeks = computed(() => Math.max(6, Math.ceil((scoreGap.value * 2.1 + 60) / Math.max(weeklyHours.value, 1))))
  const overallProgress = computed(() => Math.round(tasks.value.filter(item => item.done).length / Math.max(tasks.value.length, 1) * 100))
  const stages = computed(() => stageTemplates.map(stage => ({
    ...stage,
    status: stage.id < currentStage.value ? 'completed' : stage.id === currentStage.value ? 'active' : 'pending'
  })))

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

  function syncDiagnosticSubjects() {
    const existing = diagnostic.value.subjectScores
    diagnostic.value.subjectScores = Object.fromEntries(
      (selectedMajor.value?.subjects || []).map(subject => [subject, existing[subject] ?? 25])
    )
  }

  function completeDiagnostic(payload) {
    diagnostic.value = { ...diagnostic.value, ...payload, completed: true }
  }

  function resetDiagnostic() {
    diagnostic.value = {
      ...diagnostic.value,
      completed: false,
      answers: {},
      knowledgeDetails: [],
      correctCount: 0,
      totalQuestions: 0,
      durationSeconds: 0
    }
    syncDiagnosticSubjects()
  }

  function toggleTask(taskId) {
    const task = tasks.value.find(item => item.id === taskId)
    if (task) task.done = !task.done
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
    if (passed && currentStage.value < 4) currentStage.value += 1
    return { passed, threshold }
  }

  function advanceStage() {
    if (currentStage.value < 4) currentStage.value += 1
  }

  watch([profile, selectedInstitutionCode, diagnostic, currentStage, tasks, stageTests], () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      profile: profile.value,
      selectedInstitutionCode: selectedInstitutionCode.value,
      diagnostic: diagnostic.value,
      currentStage: currentStage.value,
      tasks: tasks.value,
      stageTests: stageTests.value
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
    weeklyHours,
    estimatedWeeks,
    overallProgress,
    stages,
    updateProfile,
    selectInstitution,
    completeDiagnostic,
    resetDiagnostic,
    toggleTask,
    submitStageTest,
    advanceStage
  }
})
