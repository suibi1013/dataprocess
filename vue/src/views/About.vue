<template>
  <div class="about-page">
    <div class="about-header">
      <h1>关于数据可视化</h1>
      <p class="version">版本 1.0.0</p>
    </div>
    
    <div class="about-content">
      <div class="info-section">
        <h2>系统介绍</h2>
        <p>
          数据可视化是一个功能强大的演示文稿转换工具，能够将Microsoft PowerPoint文件
          快速转换为现代化的HTML网页格式。系统采用Vue 3 + TypeScript技术栈开发，
          提供直观易用的用户界面和丰富的功能特性。
        </p>
      </div>
      
      <div class="features-section">
        <h2>主要功能</h2>
        <div class="features-grid">
          <div class="feature-item">
            <div class="feature-icon">🎨</div>
            <h3>模板管理</h3>
            <p>创建和管理自定义转换模板，支持多种样式和布局选项</p>
          </div>
          <div class="feature-item">
            <div class="feature-icon">📊</div>
            <h3>数据源集成</h3>
            <p>连接多种数据库，实现动态数据展示和实时更新</p>
          </div>
          <div class="feature-item">
            <div class="feature-icon">⚡</div>
            <h3>快速转换</h3>
            <p>高效的转换引擎，快速将PPT文件转换为响应式HTML页面</p>
          </div>
          <div class="feature-item">
            <div class="feature-icon">📱</div>
            <h3>响应式设计</h3>
            <p>生成的HTML页面完美适配各种设备和屏幕尺寸</p>
          </div>
        </div>
      </div>
      
      <div class="tech-section">
        <h2>技术栈</h2>
        <div class="tech-grid">
          <div class="tech-item">
            <strong>前端框架:</strong>
            <span>Vue 3 + TypeScript</span>
          </div>
          <div class="tech-item">
            <strong>路由管理:</strong>
            <span>Vue Router 4</span>
          </div>
          <div class="tech-item">
            <strong>后端服务:</strong>
            <span>Python + FastAPI</span>
          </div>
          <div class="tech-item">
            <strong>转换引擎:</strong>
            <span>python-pptx + 自定义转换器</span>
          </div>
        </div>
      </div>
      
      <div class="contact-section">
        <h2>联系信息</h2>
        <div class="contact-grid">
          <div class="contact-item">
            <div class="contact-icon">📧</div>
            <div>
              <strong>邮箱支持</strong>
              <p>support@ppt2html.com</p>
            </div>
          </div>
          <div class="contact-item">
            <div class="contact-icon">🌐</div>
            <div>
              <strong>官方网站</strong>
              <p>www.ppt2html.com</p>
            </div>
          </div>
          <div class="contact-item">
            <div class="contact-icon">📚</div>
            <div>
              <strong>文档中心</strong>
              <p>docs.ppt2html.com</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="system-info">
        <h2>系统信息</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">系统版本:</span>
            <span class="info-value">{{ systemInfo.version }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">构建时间:</span>
            <span class="info-value">{{ systemInfo.buildTime }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">运行环境:</span>
            <span class="info-value">{{ systemInfo.environment }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">浏览器:</span>
            <span class="info-value">{{ systemInfo.browser }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

interface SystemInfo {
  version: string
  buildTime: string
  environment: string
  browser: string
}

// 获取浏览器信息
function getBrowserInfo(): string {
  const userAgent = navigator.userAgent
  if (userAgent.includes('Chrome')) {
    return 'Google Chrome'
  } else if (userAgent.includes('Firefox')) {
    return 'Mozilla Firefox'
  } else if (userAgent.includes('Safari')) {
    return 'Safari'
  } else if (userAgent.includes('Edge')) {
    return 'Microsoft Edge'
  } else {
    return '未知浏览器'
  }
}

// 创建响应式状态
const state = reactive({
  systemInfo: {
    version: '1.0.0',
    buildTime: '2024-01-15 10:30:00',
    environment: 'Production',
    browser: getBrowserInfo()
  } as SystemInfo
})

// 导出模板中使用的变量
const systemInfo = state.systemInfo
</script>

<style scoped>
.about-page {
  padding: 30px;
  max-width: 1000px;
  margin: 0 auto;
  line-height: 1.6;
}

.about-header {
  text-align: center;
  margin-bottom: 40px;
  padding-bottom: 20px;
  border-bottom: 2px solid #ecf0f1;
}

.about-header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 700;
}

.version {
  color: #7f8c8d;
  font-size: 1.1rem;
  font-weight: 500;
}

.about-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.info-section,
.features-section,
.tech-section,
.contact-section,
.system-info {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.info-section h2,
.features-section h2,
.tech-section h2,
.contact-section h2,
.system-info h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.5rem;
  font-weight: 600;
}

.info-section p {
  color: #7f8c8d;
  font-size: 1.1rem;
  text-align: justify;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 25px;
}

.feature-item {
  text-align: center;
  padding: 20px;
  border: 1px solid #ecf0f1;
  border-radius: 8px;
  transition: transform 0.2s ease;
}

.feature-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 15px;
}

.feature-item h3 {
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 1.2rem;
}

.feature-item p {
  color: #7f8c8d;
  font-size: 0.95rem;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
}

.tech-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.tech-item strong {
  color: #2c3e50;
}

.tech-item span {
  color: #7f8c8d;
  font-family: 'Courier New', monospace;
}

.contact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.contact-icon {
  font-size: 2rem;
}

.contact-item strong {
  color: #2c3e50;
  display: block;
  margin-bottom: 5px;
}

.contact-item p {
  color: #7f8c8d;
  margin: 0;
  font-family: 'Courier New', monospace;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.info-label {
  color: #2c3e50;
  font-weight: 500;
}

.info-value {
  color: #7f8c8d;
  font-family: 'Courier New', monospace;
}

@media (max-width: 768px) {
  .about-page {
    padding: 20px;
  }
  
  .about-header h1 {
    font-size: 2rem;
  }
  
  .features-grid,
  .tech-grid,
  .contact-grid,
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .info-section,
  .features-section,
  .tech-section,
  .contact-section,
  .system-info {
    padding: 20px;
  }
}
</style>