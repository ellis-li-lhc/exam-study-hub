<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useApplicationStore } from './stores/application'

const store = useApplicationStore()

// 应用启动时从后端加载基础数据（失败则用本地兜底数据）
onMounted(() => {
  store.loadMajors()
  store.loadProvinces()
  store.loadInstitutions()
})
</script>

<style>
#app {
  min-height: 100vh;
}
</style>
