import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useExamStore = defineStore('exam', () => {
  // 学习计划
  const studyPlan = ref({
    dailyTasks: [],
    weeklyGoals: [],
    monthlyMilestones: []
  })

  // 各科进度
  const subjectProgress = ref({})

  // 学习记录
  const studyRecords = ref([])

  // 目标分数
  const targetScore = ref(null)

  // 当前水平评估
  const currentLevel = ref('medium') // low, medium, high

  // 生成学习计划（半自动）
  function generatePlan(subjects, targetScoreData, level = 'medium') {
    if (!subjects || subjects.length === 0) return

    targetScore.value = targetScoreData
    currentLevel.value = level

    // 根据科目和目标分数生成计划
    const dailyTasks = []
    const weeklyGoals = []
    const monthlyMilestones = []

    // 每科的学习时间分配（根据难度和分值）
    const timeAllocation = {
      '政治': { daily: 1, weekly: 7, monthly: 4 },
      '英语': { daily: 1.5, weekly: 10, monthly: 6 },
      '高等数学': { daily: 2, weekly: 14, monthly: 8 },
      '大学语文': { daily: 1, weekly: 7, monthly: 4 },
      '民法': { daily: 1.5, weekly: 10, monthly: 6 },
      '教育理论': { daily: 1.5, weekly: 10, monthly: 6 },
      '医学综合': { daily: 2, weekly: 14, monthly: 8 },
      '生态学基础': { daily: 1.5, weekly: 10, monthly: 6 }
    }

    // 为每科生成任务
    subjects.forEach(subject => {
      const allocation = timeAllocation[subject] || { daily: 1, weekly: 7, monthly: 4 }

      // 每日任务
      dailyTasks.push({
        subject,
        duration: allocation.daily,
        type: 'daily',
        tasks: generateDailyTasks(subject, level)
      })

      // 每周目标
      weeklyGoals.push({
        subject,
        duration: allocation.weekly,
        type: 'weekly',
        goals: generateWeeklyGoals(subject, level)
      })

      // 每月里程碑
      monthlyMilestones.push({
        subject,
        duration: allocation.monthly,
        type: 'monthly',
        milestones: generateMonthlyMilestones(subject, level)
      })
    })

    studyPlan.value = {
      dailyTasks,
      weeklyGoals,
      monthlyMilestones
    }

    // 初始化进度
    subjects.forEach(subject => {
      if (!subjectProgress.value[subject]) {
        subjectProgress.value[subject] = {
          completedTasks: 0,
          totalTasks: 30,
          percent: 0,
          lastStudyDate: null
        }
      }
    })
  }

  // 生成每日任务
  function generateDailyTasks(subject, level) {
    const tasksBySubject = {
      '政治': [
        '背诵核心概念 10 个',
        '做选择题 20 道',
        '阅读时政热点 1 篇',
        '整理错题 3-5 道'
      ],
      '英语': [
        '背单词 30-50 个',
        '做阅读理解 2 篇',
        '练习翻译 1 段',
        '背诵作文模板 1 个'
      ],
      '高等数学': [
        '复习公式 10 个',
        '做基础题 5 道',
        '做综合题 2 道',
        '整理错题 3 道'
      ],
      '大学语文': [
        '背诵古诗词 2 首',
        '阅读文言文 1 篇',
        '练习写作 1 段',
        '复习文学常识 10 条'
      ],
      '民法': [
        '背诵法条 5 条',
        '做案例分析 1 道',
        '复习重点概念 10 个',
        '整理错题 3 道'
      ],
      '教育理论': [
        '背诵教育学家观点 5 个',
        '做简答题 2 道',
        '复习教育心理学概念 10 个',
        '整理错题 3 道'
      ],
      '医学综合': [
        '复习解剖学知识 10 点',
        '做选择题 20 道',
        '背诵药理学名词 10 个',
        '整理错题 3 道'
      ],
      '生态学基础': [
        '复习生态学概念 10 个',
        '做选择题 15 道',
        '背诵专业名词 10 个',
        '整理错题 3 道'
      ]
    }

    const tasks = tasksBySubject[subject] || ['复习知识点', '做练习题', '整理笔记']

    // 根据水平调整任务量
    if (level === 'low') {
      return tasks.slice(0, 3)
    } else if (level === 'high') {
      return [...tasks, '做真题 1 套']
    }
    return tasks
  }

  // 生成每周目标
  function generateWeeklyGoals(subject, level) {
    const goals = [
      `完成本周${subject}学习任务 5 天以上`,
      `做${subject}专项练习题 50 道`,
      `整理${subject}错题本 1 次`,
      `复习本周学习内容 1 次`
    ]

    if (level === 'high') {
      goals.push(`做${subject}模拟题 1 套`)
    }

    return goals
  }

  // 生成每月里程碑
  function generateMonthlyMilestones(subject, level) {
    const milestones = [
      `完成${subject}基础知识复习`,
      `${subject}选择题正确率达到 70%`,
      `掌握${subject}核心考点 80%`
    ]

    if (level === 'high') {
      milestones.push(`${subject}模拟题达到目标分数`)
    }

    return milestones
  }

  // 更新进度
  function updateProgress(subject, completed = true) {
    if (!subjectProgress.value[subject]) return

    if (completed) {
      subjectProgress.value[subject].completedTasks++
    }

    const { completedTasks, totalTasks } = subjectProgress.value[subject]
    subjectProgress.value[subject].percent = Math.round((completedTasks / totalTasks) * 100)
    subjectProgress.value[subject].lastStudyDate = new Date().toISOString().split('T')[0]
  }

  // 添加学习记录
  function addStudyRecord(record) {
    studyRecords.value.push({
      ...record,
      id: Date.now(),
      timestamp: new Date().toISOString()
    })
  }

  // 总体进度
  const overallProgress = computed(() => {
    const subjects = Object.keys(subjectProgress.value)
    if (subjects.length === 0) return 0

    const totalPercent = subjects.reduce((sum, subject) => {
      return sum + (subjectProgress.value[subject]?.percent || 0)
    }, 0)

    return Math.round(totalPercent / subjects.length)
  })

  // 重置
  function reset() {
    studyPlan.value = { dailyTasks: [], weeklyGoals: [], monthlyMilestones: [] }
    subjectProgress.value = {}
    studyRecords.value = []
    targetScore.value = null
    currentLevel.value = 'medium'
  }

  return {
    studyPlan,
    subjectProgress,
    studyRecords,
    targetScore,
    currentLevel,
    overallProgress,
    generatePlan,
    updateProgress,
    addStudyRecord,
    reset
  }
})
