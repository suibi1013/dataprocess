<template>
  <nav class="navigation">
    <div class="nav-container">
      <!-- 左侧Logo -->
      <div class="nav-brand">
        <h2>数据可视化</h2>
      </div>
      
      <!-- 导航菜单 -->
      <ul v-if="isLicenseValid" class="nav-menu">
        <li class="nav-item">
          <router-link 
            to="/" 
            class="nav-link"
            :class="{ active: $route.name === 'Home' }"
          >
            首页
          </router-link>
        </li>
        <li class="nav-item">
          <router-link 
            to="/datasource" 
            class="nav-link"
            :class="{ active: $route.name === 'DataSource' }"
          >
            数据源
          </router-link>
        </li>
        <li class="nav-item">
          <router-link 
            to="/template" 
            class="nav-link"
            :class="{ active: $route.name === 'Template' }"
          >
            模板管理
          </router-link>
        </li>
        <li class="nav-item">
          <router-link 
            to="/process" 
            class="nav-link"
            :class="{ active: $route.name === 'DataProcess' }"
          >
            数据流程
          </router-link>
        </li>
        <li class="nav-item">
          <router-link 
            to="/instruction" 
            class="nav-link"
            :class="{ active: $route.name === 'Instruction' }"
          >
            指令配置
          </router-link>
        </li>
        <li class="nav-item">
          <router-link 
            to="/systeminfo" 
            class="nav-link"
            :class="{ active: $route.name === 'systeminfo' }"
          >
            系统信息
          </router-link>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

// 写死的授权码
const LICENSE_KEY = 'MjAyNy0w-Mi0xMToz-ZDIzODc5-YzMwNDAy-Yjg0OTc2-OWNkODlm-NDE2ZjZh-MGMzODZh-NWE4YjI1-YjZmZDM1-OGFmYTgw-OTFkZWFl-ZjEy'; // 生成的有效授权码

// 授权码验证状态
const isLicenseValid = ref(false);
const isLoading = ref(true);

// 调用后端接口验证授权码
const validateLicenseFromBackend = async (licenseKey: string): Promise<boolean> => {
  try {
    const response = await fetch('/api/system/license/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ license_key: licenseKey })
    });
    console.log('授权码验证接口响应:', response);
    if (!response.ok) {
      console.error('授权码验证接口请求失败:', response.status);
      return false;
    }
    
    const result = await response.json();
    console.log('后端授权码验证结果:', result);
    
    return result.success === true;
  } catch (error) {
    console.error('授权码验证失败:', error);
    return false;
  }
};

// 页面挂载时验证授权码
onMounted(async () => {
  isLoading.value = true;
  try {
    isLicenseValid.value = await validateLicenseFromBackend(LICENSE_KEY);
    console.log('授权码验证结果:', isLicenseValid.value);
  } finally {
    isLoading.value = false;
  }
});
</script>

<style scoped>
.navigation {
  background-color: #2c3e50;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
}

.nav-brand h2 {
  color: #ffffff;
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.nav-menu {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 30px;
}

.nav-item {
  position: relative;
}

.nav-link {
  color: #ecf0f1;
  text-decoration: none;
  padding: 10px 15px;
  border-radius: 4px;
  transition: all 0.3s ease;
  font-weight: 500;
  display: block;
}

.nav-link:hover {
  background-color: #34495e;
  color: #ffffff;
}

.nav-link.active {
  background-color: #3498db;
  color: #ffffff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    height: auto;
    padding: 10px 20px;
  }
  
  .nav-menu {
    margin-top: 10px;
    gap: 15px;
  }
  
  .nav-brand h2 {
    font-size: 1.2rem;
  }
}
</style>