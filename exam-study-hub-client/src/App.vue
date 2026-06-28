<template>
  <router-view />
</template>

<script setup>
// 基础数据（省份/院校）改在登录后的主框架 MainLayout 内加载：
// 这些接口需要登录态，放在未鉴权的根组件会被 401 拒绝。
</script>

<style>
#app {
  min-height: 100vh;
}
</style>
