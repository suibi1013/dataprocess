import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import Home from '../views/Home.vue'
import About from '../views/About.vue'
import Template from '../views/Template.vue'
import DataSource from '../views/DataSource.vue'
import TemplateTest from '../views/TemplateTest.vue'
import TemplateEditorView from '../views/TemplateEditor.vue'
import DataProcess from '../views/DataProcess.vue'

// 定义路由配置
const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: '首页' }
  },
  {
    path: '/template',
    name: 'Template', 
    component: Template,
    meta: { title: '模板管理' }
  },
  {
    path: '/template/editor',
    name: 'template-editor',
    component: TemplateEditorView,
    props: (route) => ({ templateId: route.query.template })
  },
  {
    path: '/datasource',
    name: 'DataSource',
    component: DataSource,
    meta: { title: '数据源' }
  },
  {
    path: '/instruction',
    name: 'Instruction',
    component: () => import('../views/Instruction.vue'),
    meta: { title: '指令管理' }
  },
  {
    path: '/about',
    name: 'About',
    component: About,
    meta: { title: '关于' }
  },
  {
    path: '/process',
    name: 'DataProcess',
    component: DataProcess,
    meta: { title: '流程管理' }
  },
  {
    path: '/template-test',
    name: 'TemplateTest',
    component: TemplateTest,
    meta: { title: '模板测试' }
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHashHistory(process.env.BASE_URL),
  routes
})

export default router