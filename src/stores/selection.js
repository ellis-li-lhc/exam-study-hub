import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '../api'

export const useSelectionStore = defineStore('selection', () => {
  // 当前步骤
  const currentStep = ref(0)

  // 选择状态
  const selectedProvince = ref(null)
  const selectedCity = ref(null)
  const selectedUniversity = ref(null)
  const selectedMajor = ref(null)

  // 选项列表
  const provinces = ref([])
  const cities = ref([])
  const universities = ref([])
  const majors = ref([])

  // 加载状态
  const loading = ref(false)

  // 是否完成选择
  const isComplete = computed(() => {
    return selectedProvince.value &&
           selectedCity.value &&
           selectedUniversity.value &&
           selectedMajor.value
  })

  // 当前选择的摘要
  const selectionSummary = computed(() => {
    if (!isComplete.value) return null
    return {
      province: provinces.value.find(p => p.code === selectedProvince.value)?.name,
      city: cities.value.find(c => c.code === selectedCity.value)?.name,
      university: universities.value.find(u => u.code === selectedUniversity.value)?.name,
      major: majors.value.find(m => m.code === selectedMajor.value)?.name
    }
  })

  // 加载省份列表
  async function loadProvinces() {
    loading.value = true
    try {
      provinces.value = await api.getProvinces()
    } finally {
      loading.value = false
    }
  }

  // 选择省份并加载城市
  async function selectProvince(provinceCode) {
    selectedProvince.value = provinceCode
    selectedCity.value = null
    selectedUniversity.value = null
    selectedMajor.value = null
    cities.value = []
    universities.value = []
    majors.value = []

    loading.value = true
    try {
      cities.value = await api.getCitiesByProvince(provinceCode)
      currentStep.value = 1
    } finally {
      loading.value = false
    }
  }

  // 选择城市并加载大学
  async function selectCity(cityCode) {
    selectedCity.value = cityCode
    selectedUniversity.value = null
    selectedMajor.value = null
    universities.value = []
    majors.value = []

    loading.value = true
    try {
      universities.value = await api.getUniversitiesByCity(cityCode)
      currentStep.value = 2
    } finally {
      loading.value = false
    }
  }

  // 选择大学并加载专业
  async function selectUniversity(universityCode) {
    selectedUniversity.value = universityCode
    selectedMajor.value = null
    majors.value = []

    loading.value = true
    try {
      majors.value = await api.getMajorsByUniversity(universityCode)
      currentStep.value = 3
    } finally {
      loading.value = false
    }
  }

  // 选择专业
  function selectMajor(majorCode) {
    selectedMajor.value = majorCode
    currentStep.value = 4
  }

  // 重置选择
  function reset() {
    currentStep.value = 0
    selectedProvince.value = null
    selectedCity.value = null
    selectedUniversity.value = null
    selectedMajor.value = null
    cities.value = []
    universities.value = []
    majors.value = []
  }

  // 返回上一步
  function goBack() {
    if (currentStep.value > 0) {
      currentStep.value--
      if (currentStep.value === 2) {
        selectedMajor.value = null
        majors.value = []
      } else if (currentStep.value === 1) {
        selectedUniversity.value = null
        selectedMajor.value = null
        universities.value = []
        majors.value = []
      } else if (currentStep.value === 0) {
        selectedCity.value = null
        selectedUniversity.value = null
        selectedMajor.value = null
        cities.value = []
        universities.value = []
        majors.value = []
      }
    }
  }

  return {
    currentStep,
    selectedProvince,
    selectedCity,
    selectedUniversity,
    selectedMajor,
    provinces,
    cities,
    universities,
    majors,
    loading,
    isComplete,
    selectionSummary,
    loadProvinces,
    selectProvince,
    selectCity,
    selectUniversity,
    selectMajor,
    reset,
    goBack
  }
})
