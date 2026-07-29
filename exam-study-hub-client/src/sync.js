// 云端同步：登录后把本地状态与服务器对齐，并在本地变更时自动回写。
// 三块状态分别对应三个 localStorage key，与后端 user_states 的三个 JSON 字段一一对应。
import { watch } from 'vue'
import { ElMessage } from 'element-plus'
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
let retryTimer = null
let cloudVersion = 0
let conflictNotified = false
let changeSequence = 0
let syncedSequence = 0
let activeSave = null

function snapshotForSave() {
  return {
    ...localSnapshot(),
    client_version: cloudVersion
  }
}

function hasUnsyncedChanges() {
  return changeSequence > syncedSequence
}

function queuePush(delay = 1500) {
  clearTimeout(pushTimer)
  pushTimer = setTimeout(() => {
    pushTimer = null
    void persistPendingChanges('auto')
  }, delay)
}

// 只保存尚未同步的变更；序号可避免保存过程中产生的新修改被误标记为已同步。
async function persistPendingChanges(context) {
  if (!hasUnsyncedChanges()) return true
  if (activeSave) {
    await activeSave
    if (!hasUnsyncedChanges()) return true
  }

  const targetSequence = changeSequence
  const operation = (async () => {
    try {
      const saved = await saveState(snapshotForSave())
      cloudVersion = saved.sync_version ?? cloudVersion
      syncedSequence = Math.max(syncedSequence, targetSequence)
      conflictNotified = false
      clearTimeout(retryTimer)
      if (hasUnsyncedChanges()) queuePush()
      return true
    } catch (error) {
      if (error.status === 409) {
        console.warn('云端状态版本冲突，已拉取最新进度', error)
        const pulled = await pullFromCloud()
        if (pulled) syncedSequence = changeSequence
        if (context === 'exit') {
          ElMessage.warning('云端进度已在其他设备更新，退出前已刷新到最新版本')
        } else if (!conflictNotified) {
          ElMessage.warning('云端进度已在其他设备更新，已为你刷新到最新版本')
          conflictNotified = true
        }
        return false
      }
      if (context === 'exit') {
        console.warn('退出前云端保存失败', error)
        ElMessage.warning('退出前云端保存失败，当前进度仍保留在本机')
      } else {
        ElMessage.warning('云端保存失败，当前进度已保留在本机，稍后会自动重试')
        console.warn('云端保存失败（已保留在本地，稍后重试）', error)
        clearTimeout(retryTimer)
        retryTimer = setTimeout(() => queuePush(0), 10000)
      }
      return false
    }
  })()

  activeSave = operation
  try {
    return await operation
  } finally {
    if (activeSave === operation) activeSave = null
  }
}

// 防抖回写：本地变更后 1.5s 内无新变更才真正发请求，避免频繁打服务器。
function schedulePush() {
  changeSequence += 1
  queuePush()
}

// 退出登录或关键操作前调用：立即刷一次云端，减少防抖窗口内的数据丢失。
export async function flushCloudState() {
  clearTimeout(pushTimer)
  pushTimer = null
  clearTimeout(retryTimer)
  retryTimer = null
  return persistPendingChanges('exit')
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
    return false
  }

  cloudVersion = cloud.sync_version ?? 0
  const hasCloud = cloud.app_state || cloud.english_extras || cloud.vocab_progress
  if (hasCloud) {
    if (cloud.app_state) appStore.hydrate(cloud.app_state)
    if (cloud.english_extras) engStore.hydrate(cloud.english_extras)
    if (cloud.vocab_progress) vocabStore.hydrate(cloud.vocab_progress)
  } else {
    // 云端还没有数据：把本地现有进度作为初始数据上传。
    try {
      const saved = await saveState(snapshotForSave())
      cloudVersion = saved.sync_version ?? cloudVersion
    } catch (error) {
      console.warn('初始状态上传失败', error)
    }
  }
  syncedSequence = changeSequence
  return true
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
      appStore.tasksVersion,
      appStore.stageTests,
      appStore.tasksDate,
      appStore.reviewQueue,
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
  clearTimeout(retryTimer)
}

// 退出登录：停止同步并清空本地状态，避免下个账号看到上个账号的数据。
export function clearLocalState() {
  stopAutoSync()
  cloudVersion = 0
  conflictNotified = false
  changeSequence = 0
  syncedSequence = 0
  useApplicationStore().resetAll()
  useEnglishProgressStore().resetAll()
  useVocabularyStore().resetAll()
  localStorage.removeItem(LS.app)
  localStorage.removeItem(LS.eng)
  localStorage.removeItem(LS.vocab)
}
