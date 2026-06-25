import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

// 通用学习进度：用带前缀的字符串 key 记录“已掌握”项，
// 供造句基础(ess)、核心短语(phr)、基础语法(gra)共用，持久化到 localStorage。
const STORAGE_KEY = 'english-extras-progress'

function loadSaved() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}
  } catch {
    return {}
  }
}

export const useEnglishProgressStore = defineStore('englishProgress', () => {
  const saved = loadSaved()
  const knownKeys = ref(new Set(saved.knownKeys || []))

  function isKnown(key) {
    return knownKeys.value.has(key)
  }

  function toggle(key) {
    const next = new Set(knownKeys.value)
    if (next.has(key)) next.delete(key)
    else next.add(key)
    knownKeys.value = next
  }

  function markMany(keys, known) {
    const next = new Set(knownKeys.value)
    keys.forEach(key => known ? next.add(key) : next.delete(key))
    knownKeys.value = next
  }

  function countKnown(keys) {
    return keys.filter(key => knownKeys.value.has(key)).length
  }

  function resetPrefix(prefix) {
    knownKeys.value = new Set([...knownKeys.value].filter(key => !key.startsWith(prefix)))
  }

  watch(knownKeys, () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ knownKeys: [...knownKeys.value] }))
  }, { deep: true })

  return { knownKeys, isKnown, toggle, markMany, countKnown, resetPrefix }
})
