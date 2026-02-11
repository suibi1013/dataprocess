<template>
  <div class="SystemInfo-page">    
    <div class="SystemInfo-content">
      <div class="info-section">
        <h2>系统介绍</h2>
        <p>
          数据可视化是一个功能强大的数据管理和流程可视化设计工具，提供直观易用的用户界面和丰富的功能特性。
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
            <div class="feature-icon">👀</div>
            <h3>数据流程可视</h3>
            <p>灵活清晰的数据流程可视化设计，支持节点指令配置</p>
          </div>
        </div>
      </div>      
      
      <div class="version-history-section">
        <h2>系统版本更新记录</h2>
        <div class="version-list">
          <div 
            v-for="version in versionHistory" 
            :key="version.version"
            class="version-item"
          >
            <div class="version-header">
              <h3 class="version-number">{{ version.version }}</h3>
              <span class="version-date">{{ version.date }}</span>
            </div>
            <div class="version-changes">
              <ul>
                <li v-for="(change, index) in version.changes" :key="index">
                  {{ change }}
                </li>
              </ul>
            </div>
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
              <p>support@dataprocess.com</p>
            </div>
          </div>
          <div class="contact-item">
            <div class="contact-icon">🌐</div>
            <div>
              <strong>官方网站</strong>
              <p>www.dataprocess.com</p>
            </div>
          </div>
          <div class="contact-item">
            <div class="contact-icon">📚</div>
            <div>
              <strong>文档中心</strong>
              <p>docs.dataprocess.com</p>
            </div>
          </div>
        </div>
      </div>      
    </div>
  </div>
</template>

<script setup lang="ts">
import { versionHistory } from '../data/versionHistory';
</script>

<style scoped>
/* 原有样式保持不变 */
.SystemInfo-page {
  padding: 30px;
  max-width: 1000px;
  margin: 0 auto;
  line-height: 1.6;
}

.SystemInfo-header {
  text-align: center;
  margin-bottom: 40px;
  padding-bottom: 20px;
  border-bottom: 2px solid #ecf0f1;
}

.SystemInfo-header h1 {
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

.SystemInfo-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.info-section,
.features-section,
.tech-section,
.contact-section,
.system-info,
.version-history-section {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.info-section h2,
.features-section h2,
.tech-section h2,
.contact-section h2,
.system-info h2,
.version-history-section h2 {
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



/* 版本更新记录样式 */
.version-list {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.version-item {
  border: 1px solid #ecf0f1;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s ease;
}

.version-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ecf0f1;
}

.version-number {
  color: #3498db;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
}

.version-date {
  color: #7f8c8d;
  font-size: 0.9rem;
  font-family: 'Courier New', monospace;
}

.version-changes ul {
  margin: 0;
  padding-left: 20px;
}

.version-changes li {
  color: #2c3e50;
  margin-bottom: 8px;
  line-height: 1.5;
}

.version-changes li:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .SystemInfo-page {
    padding: 20px;
  }
  
  .SystemInfo-header h1 {
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
  .system-info,
  .version-history-section {
    padding: 20px;
  }
  
  .version-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>