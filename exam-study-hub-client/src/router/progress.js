import { ref } from 'vue'

export const routeLoading = ref(false)

export function startRouteLoading() {
  routeLoading.value = true
}

export function finishRouteLoading() {
  routeLoading.value = false
}
