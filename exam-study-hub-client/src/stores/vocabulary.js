import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import vocabulary from '../../docs/EnglishVocabulary.json'

const STORAGE_KEY = 'english-vocab-progress'
const BATCH_SIZE = 50

function loadSaved() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}
  } catch {
    return {}
  }
}

export const useVocabularyStore = defineStore('vocabulary', () => {
  const words = vocabulary.words
  const saved = loadSaved()
  const knownIds = ref(new Set(saved.knownIds || []))
  const currentBatch = ref(saved.currentBatch || 0)

  const batchSize = BATCH_SIZE
  const totalCount = words.length
  const batchCount = Math.ceil(totalCount / batchSize)

  const knownCount = computed(() => knownIds.value.size)
  const masteryPercent = computed(() => totalCount ? Math.round(knownCount.value / totalCount * 100) : 0)
  const currentWords = computed(() => words.slice(currentBatch.value * batchSize, currentBatch.value * batchSize + batchSize))
  const currentBatchKnown = computed(() => currentWords.value.filter(word => knownIds.value.has(word.id)).length)
  const batchOptions = computed(() => Array.from({ length: batchCount }, (_, index) => {
    const start = index * batchSize + 1
    const end = Math.min((index + 1) * batchSize, totalCount)
    return { value: index, label: `第 ${index + 1} 组 · ${start}-${end}` }
  }))

  function isKnown(id) {
    return knownIds.value.has(id)
  }

  function toggleKnown(id) {
    const next = new Set(knownIds.value)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    knownIds.value = next
  }

  function setBatch(index) {
    currentBatch.value = Math.max(0, Math.min(batchCount - 1, index))
  }

  function markCurrentBatch(known) {
    const next = new Set(knownIds.value)
    currentWords.value.forEach(word => known ? next.add(word.id) : next.delete(word.id))
    knownIds.value = next
  }

  function resetProgress() {
    knownIds.value = new Set()
    currentBatch.value = 0
  }

  // —— 云端同步用 ——
  function hydrate(blob) {
    if (blob && Array.isArray(blob.knownIds)) knownIds.value = new Set(blob.knownIds)
    if (blob && typeof blob.currentBatch === 'number') currentBatch.value = blob.currentBatch
  }

  function resetAll() {
    knownIds.value = new Set()
    currentBatch.value = 0
  }

  watch([knownIds, currentBatch], () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      knownIds: [...knownIds.value],
      currentBatch: currentBatch.value
    }))
  }, { deep: true })

  return {
    words,
    batchSize,
    totalCount,
    batchCount,
    knownCount,
    masteryPercent,
    currentBatch,
    currentWords,
    currentBatchKnown,
    batchOptions,
    isKnown,
    toggleKnown,
    setBatch,
    markCurrentBatch,
    resetProgress,
    hydrate,
    resetAll
  }
})
