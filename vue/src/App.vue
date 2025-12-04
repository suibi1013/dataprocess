<template>
  <div id="app">
    <!-- 页面头部 - 导航菜单 -->
    <header class="app-header">
      <Navigation />
    </header>
    
    <!-- 页面内容 - 路由视图 -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import Navigation from './components/Navigation.vue'
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f5f6fa;
  color: #2c3e50;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 页面头部样式 */
.app-header {
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 1000;
}

/* 页面主体内容样式 */
.app-main {
  flex: 1;
  background-color: #f5f6fa;
  min-height: calc(100vh - 60px);
  overflow-y: auto;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-main {
    min-height: calc(100vh - 80px);
  }
}
</style>
