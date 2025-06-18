# Pinia 详细使用教程

Pinia 是 Vue.js 的下一代状态管理库，由 Vue.js 核心团队成员开发，旨在提供一个更简单、更直观的状态管理解决方案。相比 Vuex，Pinia 提供了更好的 TypeScript 支持、更简洁的 API 和更好的模块化设计。

## 1. 安装 Pinia

首先，你需要安装 Pinia：

```bash
npm install pinia
# 或者
yarn add pinia
# 或者
pnpm add pinia
```

## 2. 基本配置

在你的 Vue 应用中引入并使用 Pinia：

```javascript
// main.js 或 main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.mount('#app')
```

## 3. 创建 Store

Pinia 使用 `defineStore` 函数来定义一个 store。每个 store 都是一个独立的模块。

### 3.1 选项式 Store

```javascript
// stores/counter.js
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', {
  state: () => ({
    count: 0
  }),
  getters: {
    doubleCount: (state) => state.count * 2
  },
  actions: {
    increment() {
      this.count++
    }
  }
})
```

### 3.2 组合式 Store (推荐)

```javascript
// stores/counter.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  function increment() {
    count.value++
  }

  return { count, doubleCount, increment }
})
```

## 4. 在组件中使用 Store

### 4.1 基本使用

```vue
<script setup>
import { useCounterStore } from '@/stores/counter'

const counter = useCounterStore()
</script>

<template>
  <div>
    <p>Count: {{ counter.count }}</p>
    <p>Double count: {{ counter.doubleCount }}</p>
    <button @click="counter.increment()">Increment</button>
  </div>
</template>
```

### 4.2 解构 Store

如果需要解构 store 的属性，需要使用 `storeToRefs` 来保持响应性：

```vue
<script setup>
import { storeToRefs } from 'pinia'
import { useCounterStore } from '@/stores/counter'

const counter = useCounterStore()
// 使用 storeToRefs 保持响应性
const { count, doubleCount } = storeToRefs(counter)
// 方法可以直接解构，不需要 storeToRefs
const { increment } = counter
</script>

<template>
  <div>
    <p>Count: {{ count }}</p>
    <p>Double count: {{ doubleCount }}</p>
    <button @click="increment()">Increment</button>
  </div>
</template>
```

## 5. State

### 5.1 访问和修改 State

```javascript
const counter = useCounterStore()

// 访问 state
console.log(counter.count)

// 直接修改
counter.count++

// 使用 $patch 批量修改
counter.$patch({
  count: counter.count + 1,
  // 其他 state 修改
})

// 使用 $patch 带函数的版本
counter.$patch((state) => {
  state.count++
  // 其他修改
})

// 重置 state
counter.$reset()
```

### 5.2 订阅 State 变化

```javascript
counter.$subscribe((mutation, state) => {
  // mutation 包含修改的信息
  // state 是修改后的状态
  console.log('状态变化:', mutation, state)
})
```

## 6. Getters

Getters 是 store 的计算属性，它们接收 state 作为第一个参数：

```javascript
export const useCounterStore = defineStore('counter', {
  state: () => ({
    count: 0
  }),
  getters: {
    doubleCount: (state) => state.count * 2,
    // 使用其他 getter
    doubleCountPlusOne() {
      return this.doubleCount + 1
    }
  }
})
```

## 7. Actions

Actions 相当于组件中的 methods，可以包含异步操作：

```javascript
export const useUserStore = defineStore('user', {
  state: () => ({
    user: null
  }),
  actions: {
    async fetchUser(userId) {
      try {
        const response = await fetch(`/api/users/${userId}`)
        this.user = await response.json()
      } catch (error) {
        console.error('获取用户失败:', error)
      }
    }
  }
})
```

## 8. 插件

Pinia 支持插件来扩展功能：

```javascript
// 定义一个插件
function myPiniaPlugin(context) {
  console.log('Store:', context.store)
  console.log('App:', context.app)
  console.log('Options:', context.options)
  
  // 可以添加 state
  context.store.customProperty = 'hello'
  
  // 可以添加 action
  context.store.customAction = () => {
    console.log('Custom action called')
  }
  
  // 可以监听 state 变化
  context.store.$subscribe((mutation, state) => {
    console.log('State changed:', state)
  })
  
  // 可以监听 action
  context.store.$onAction((action) => {
    console.log('Action started:', action.name)
    action.after(() => {
      console.log('Action finished:', action.name)
    })
    action.onError((error) => {
      console.log('Action failed:', action.name, error)
    })
  })
}

// 使用插件
const pinia = createPinia()
pinia.use(myPiniaPlugin)
```

## 9. 服务端渲染 (SSR)

Pinia 支持服务端渲染：

```javascript
// 在 SSR 环境中
export default {
  // ...
  setup() {
    // 在 setup 中调用 useStore()
    const store = useStore()
    // 因为 pinia 实例是 setup 中的活动实例，
    // 所以不需要传递 `pinia` 实例
  }
}
```

## 10. 与其他 Store 交互

```javascript
import { useUserStore } from './user-store'
import { useCartStore } from './cart-store'

export const useOrderStore = defineStore('order', {
  actions: {
    async placeOrder() {
      const user = useUserStore()
      const cart = useCartStore()
      
      if (!user.isLoggedIn) {
        throw new Error('User must be logged in')
      }
      
      const order = {
        userId: user.id,
        items: cart.items,
        total: cart.total
      }
      
      // 发送订单到服务器...
    }
  }
})
```

## 11. 测试 Store

Pinia 的 store 很容易测试：

```javascript
import { setActivePinia, createPinia } from 'pinia'
import { useCounterStore } from './counter'

describe('Counter Store', () => {
  beforeEach(() => {
    // 创建一个新的 pinia 实例并设置为活动状态
    setActivePinia(createPinia())
  })

  it('increments', () => {
    const counter = useCounterStore()
    expect(counter.count).toBe(0)
    counter.increment()
    expect(counter.count).toBe(1)
  })
})
```

## 12. 持久化存储

可以使用插件实现状态持久化：

```javascript
import { PiniaPluginContext } from 'pinia'

function persistPlugin(context: PiniaPluginContext) {
  const key = `pinia-${context.store.$id}`
  const savedState = localStorage.getItem(key)
  if (savedState) {
    context.store.$patch(JSON.parse(savedState))
  }
  
  context.store.$subscribe((mutation, state) => {
    localStorage.setItem(key, JSON.stringify(state))
  })
}

const pinia = createPinia()
pinia.use(persistPlugin)
```

或者使用现成的库 `pinia-plugin-persistedstate`:

```bash
npm install pinia-plugin-persistedstate
```

```javascript
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

// 在 store 中启用
export const useStore = defineStore('store', {
  state: () => ({ saved: '' }),
  persist: true
})
```

## 13. 与 Vue Router 集成

可以在路由导航守卫中使用 store：

```javascript
import { createRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  // ...
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return '/login'
  }
})
```

## 14. 与 Devtools 集成

Pinia 与 Vue Devtools 集成良好，只需确保安装了最新版本的 Vue Devtools 即可。

## 15. 最佳实践

1. **模块化设计**：为应用的每个功能域创建单独的 store
2. **组合式 API**：优先使用组合式风格的 store
3. **避免过度使用**：不是所有状态都需要放在 store 中，组件本地状态仍然有用
4. **命名规范**：使用 `useXxxStore` 的命名约定
5. **TypeScript**：充分利用 Pinia 优秀的 TypeScript 支持

## 总结

Pinia 提供了一个现代化、简洁且强大的状态管理解决方案，特别适合 Vue 3 应用。它的 API 设计直观，学习曲线平缓，同时提供了强大的功能如 TypeScript 支持、模块化设计和插件系统。通过本教程，你应该能够开始在项目中使用 Pinia 来管理应用状态了。