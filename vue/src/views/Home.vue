<template>
  <div class="home">
    <div class="hero-section">
      <h1>欢迎使用数据可视化</h1>
      <p class="hero-description">
        这是一个功能强大的PPT转HTML工具，帮助您轻松将PowerPoint演示文稿转换为网页格式。
      </p>
      <div class="feature-cards">
        <div class="card">
          <h3>🎨 模板管理</h3>
          <p>管理和自定义您的PPT转换模板</p>
          <router-link to="/template" class="card-link">前往模板管理</router-link>
        </div>
        <div class="card">
          <h3>📊 数据源</h3>
          <p>配置和管理您的数据源连接</p>
          <router-link to="/datasource" class="card-link">前往数据源</router-link>
        </div>
        <div class="card">
          <h3>ℹ️ 系统信息</h3>
          <p>了解更多关于系统的信息</p>
          <router-link to="/about" class="card-link">查看详情</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Vue 3 组合式 API
</script>

<style scoped>
.home {
  padding: 40px 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.hero-section {
  text-align: center;
  margin-bottom: 60px;
}

.hero-section h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 20px;
  font-weight: 700;
}

.hero-description {
  font-size: 1.2rem;
  color: #7f8c8d;
  margin-bottom: 40px;
  line-height: 1.6;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  margin-top: 40px;
}

.card {
  background: #ffffff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid #e1e8ed;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.card h3 {
  font-size: 1.4rem;
  color: #2c3e50;
  margin-bottom: 15px;
  font-weight: 600;
}

.card p {
  color: #7f8c8d;
  margin-bottom: 20px;
  line-height: 1.5;
}

.card-link {
  display: inline-block;
  background-color: #3498db;
  color: white;
  padding: 10px 20px;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background-color 0.3s ease;
}

.card-link:hover {
  background-color: #2980b9;
}

@media (max-width: 768px) {
  .hero-section h1 {
    font-size: 2rem;
  }
  
  .hero-description {
    font-size: 1rem;
  }
  
  .feature-cards {
    grid-template-columns: 1fr;
  }
}
</style>