const { contextBridge, ipcRenderer } = require('electron');

// 向渲染进程暴露安全的API
contextBridge.exposeInMainWorld('electronAPI', {
  // 获取应用版本
  getAppVersion: () => ipcRenderer.sendSync('get-app-version'),
  
  // API请求功能
  apiRequest: (url, method, data, headers) => {
    return ipcRenderer.invoke('api-request', { url, method, data, headers });
  },
  
  // 文件上传功能
  uploadFile: (url, formData) => {
    return ipcRenderer.invoke('upload-file', { url, formData });
  }
});

// 禁用开发者工具警告
process.env.ELECTRON_DISABLE_SECURITY_WARNINGS = '1';