import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      dts: false,
      resolvers: [ElementPlusResolver({ importStyle: 'css' })],
    }),
    Components({
      dts: false,
      resolvers: [ElementPlusResolver({ importStyle: 'css', directives: true })],
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          const normalized = id.replaceAll('\\', '/')
          if (normalized.includes('/node_modules/@element-plus/icons-vue/')) return 'element-icons'
          if (normalized.includes('/node_modules/element-plus/')) {
            const match = normalized.match(/\/node_modules\/element-plus\/es\/components\/([^/]+)/)
            if (match) return `el-${match[1]}`
            return 'element-core'
          }
          if (normalized.includes('/node_modules/@element-plus/')) return 'element-core'
          if (
            normalized.includes('/node_modules/vue/')
            || normalized.includes('/node_modules/vue-router/')
            || normalized.includes('/node_modules/pinia/')
            || normalized.includes('/node_modules/@vue/')
          ) return 'vue-vendor'
          if (normalized.includes('/node_modules/echarts/') || normalized.includes('/node_modules/zrender/')) return 'charts'
          if (normalized.includes('/node_modules/axios/')) return 'http-vendor'
          return 'vendor'
        },
      },
    },
  },
  server: {
    proxy: {
      // 开发期把以 /api 开头的请求转发到后端，避免跨域和硬编码地址
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
