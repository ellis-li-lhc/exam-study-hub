import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '../api'

export const useScoresStore = defineStore('scores', () => {
  const historicalScores = ref([])
  const examSubjects = ref([])
  const universityInfo = ref(null)
  const majorInfo = ref(null)
  const loading = ref(false)

  // 分数趋势分析
  const scoreTrend = computed(() => {
    if (historicalScores.value.length < 2) return null

    const sorted = [...historicalScores.value].sort((a, b) => a.year - b.year)
    const first = sorted[0]
    const last = sorted[sorted.length - 1]

    return {
      yearRange: `${first.year}-${last.year}`,
      minScoreChange: last.minScore - first.minScore,
      maxScoreChange: last.maxScore - first.maxScore,
      avgScoreChange: last.avgScore - first.avgScore,
      trend: last.avgScore > first.avgScore ? 'rising' : 'falling'
    }
  })

  // 最新一年的分数
  const latestScores = computed(() => {
    if (historicalScores.value.length === 0) return null
    return historicalScores.value.reduce((latest, current) =>
      current.year > latest.year ? current : latest
    )
  })

  // 分数统计
  const scoreStats = computed(() => {
    if (historicalScores.value.length === 0) return null

    const scores = historicalScores.value
    const avgScores = scores.map(s => s.avgScore)
    const minScores = scores.map(s => s.minScore)
    const maxScores = scores.map(s => s.maxScore)

    return {
      avgMin: Math.min(...minScores),
      avgMax: Math.max(...maxScores),
      avgMean: Math.round(avgScores.reduce((a, b) => a + b, 0) / avgScores.length),
      totalYears: scores.length
    }
  })

  // 加载目标大学和专业的数据
  async function loadTargetData(universityCode, majorCode) {
    loading.value = true
    try {
      const [scores, subjects, uniInfo, majorInfoResult] = await Promise.all([
        api.getHistoricalScores(universityCode, majorCode),
        api.getExamSubjects(majorCode),
        api.getUniversityInfo(universityCode),
        api.getMajorInfo(majorCode)
      ])

      historicalScores.value = scores
      examSubjects.value = subjects
      universityInfo.value = uniInfo
      majorInfo.value = majorInfoResult
    } finally {
      loading.value = false
    }
  }

  // 计算目标分数（基于历史数据）
  function calculateTargetScore(currentLevel = 'medium') {
    if (!latestScores.value) return null

    const { minScore, maxScore, avgScore } = latestScores.value
    const range = maxScore - minScore

    switch (currentLevel) {
      case 'low':
        // 目标：达到平均分
        return {
          target: avgScore,
          label: '稳妥线',
          description: '达到往年平均分，录取概率较大'
        }
      case 'medium':
        // 目标：平均分以上
        return {
          target: Math.round(avgScore + range * 0.2),
          label: '冲刺线',
          description: '高于往年平均分，录取概率很高'
        }
      case 'high':
        // 目标：最高分附近
        return {
          target: Math.round(maxScore - range * 0.1),
          label: '保底线',
          description: '接近往年最高分，基本确保录取'
        }
      default:
        return {
          target: avgScore,
          label: '稳妥线',
          description: '达到往年平均分，录取概率较大'
        }
    }
  }

  // 清空数据
  function clear() {
    historicalScores.value = []
    examSubjects.value = []
    universityInfo.value = null
    majorInfo.value = null
  }

  return {
    historicalScores,
    examSubjects,
    universityInfo,
    majorInfo,
    loading,
    scoreTrend,
    latestScores,
    scoreStats,
    loadTargetData,
    calculateTargetScore,
    clear
  }
})
