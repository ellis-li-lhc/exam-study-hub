// 云端同步：登录后把本地状态与服务器对齐，并在本地变更时自动回写。
// 三块状态分别对应三个 localStorage key，与后端 user_states 的三个 JSON 字段一一对应。
import { watch } from 'vue'
import { getState, saveState } from './api'
import { useApplicationStore } from './stores/application'
import { useEnglishProgressStore } from './stores/englishProgress'
import { useVocabularyStore } from './stores/vocabulary'

const LS = {
  app: 'adult-upgrade-mvp-state',
  eng: 'english-extras-progress',
  vocab: 'english-vocab-progress'
}

function readLS(key) {
  try {
    return JSON.parse(localStorage.getItem(key)) || null
  } catch {
    return null
  }
}

// 读取当前本地三块状态的快照（store 的 watch 已实时写入 localStorage，这里直接读）。
function localSnapshot() {
  return {
    app_state: readLS(LS.app),
    english_extras: readLS(LS.eng),
    vocab_progress: readLS(LS.vocab)
  }
}

let stopWatch = null
let pushTimer = null

// 防抖回写：本地变更后 1.5s 内无新变更才真正发请求，避免频繁打服务器。
function schedulePush() {
  clearTimeout(pushTimer)
  pushTimer = setTimeout(async () => {
    try {
      await saveState(localSnapshot())
    } catch (error) {
      console.warn('云端保存失败（已保留在本地，稍后重试）', error)
    }
  }, 1500)
}

// 登录后调用：用云端数据覆盖本地；若云端为空则把本地推上去（首次登录的迁移）。
export async function pullFromCloud() {
  const appStore = useApplicationStore()
  const engStore = useEnglishProgressStore()
  const vocabStore = useVocabularyStore()

  let cloud
  try {
    cloud = await getState()
  } catch (error) {
    console.warn('云端状态拉取失败，继续使用本地数据', error)
    return
  }

  const hasCloud = cloud.app_state || cloud.english_extras || cloud.vocab_progress
  if (hasCloud) {
    if (cloud.app_state) appStore.hydrate(cloud.app_state)
    if (cloud.english_extras) engStore.hydrate(cloud.english_extras)
    if (cloud.vocab_progress) vocabStore.hydrate(cloud.vocab_progress)
  } else {
    // 云端还没有数据：把本地现有进度作为初始数据上传。
    try {
      await saveState(localSnapshot())
    } catch (error) {
      console.warn('初始状态上传失败', error)
    }
  }
}

// 开启自动回写：监听三个 store 的变化，防抖推送到云端。
export function startAutoSync() {
  if (stopWatch) return
  const appStore = useApplicationStore()
  const engStore = useEnglishProgressStore()
  const vocabStore = useVocabularyStore()

  stopWatch = watch(
    () => [
      appStore.profile,
      appStore.selectedInstitutionCode,
      appStore.diagnostic,
      appStore.currentStage,
      appStore.tasks,
      appStore.stageTests,
      engStore.knownKeys,
      vocabStore.knownIds,
      vocabStore.currentBatch
    ],
    schedulePush,
    { deep: true }
  )
}

// 关闭自动回写（退出登录时）。
export function stopAutoSync() {
  if (stopWatch) {
    stopWatch()
    stopWatch = null
  }
  clearTimeout(pushTimer)
}

// 退出登录：停止同步并清空本地状态，避免下个账号看到上个账号的数据。
export function clearLocalState() {
  stopAutoSync()
  useApplicationStore().resetAll()
  useEnglishProgressStore().resetAll()
  useVocabularyStore().resetAll()
  localStorage.removeItem(LS.app)
  localStorage.removeItem(LS.eng)
  localStorage.removeItem(LS.vocab)
}
