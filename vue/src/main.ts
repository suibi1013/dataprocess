import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { pinia } from './store'

// 引入Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
// 引入中文语言包
import zhCn from 'element-plus/es/locale/lang/zh-cn'

// 引入全局样式
import './styles/dataSource.css'

// 创建Vue应用实例
const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用Element Plus
app.use(ElementPlus, { locale: zhCn })

// 使用Pinia状态管理
app.use(pinia)

// 使用路由
app.use(router)

// 挂载应用
app.mount('#app')
