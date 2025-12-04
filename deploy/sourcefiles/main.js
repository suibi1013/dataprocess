const { app, BrowserWindow, Menu} = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// 完全禁用硬件加速并使用软件渲染
app.disableHardwareAcceleration();

// 禁用GPU渲染和所有硬件加速功能
app.commandLine.appendSwitch('disable-gpu');
app.commandLine.appendSwitch('disable-gpu-compositing');
app.commandLine.appendSwitch('disable-gpu-process');
app.commandLine.appendSwitch('disable-gpu-rasterization');
app.commandLine.appendSwitch('disable-gpu-sandbox');

// 强制使用软件渲染
app.commandLine.appendSwitch('use-gl', 'swiftshader'); // 强制使用软件OpenGL实现
app.commandLine.appendSwitch('use-skia-renderer'); // 启用Skia软件渲染
app.commandLine.appendSwitch('disable-software-rasterizer', 'false'); // 确保软件光栅化器启用

// 禁用所有加速功能
app.commandLine.appendSwitch('disable-accelerated-2d-canvas');
app.commandLine.appendSwitch('disable-accelerated-compositing');
app.commandLine.appendSwitch('disable-accelerated-layers');
app.commandLine.appendSwitch('disable-accelerated-video-decode');
app.commandLine.appendSwitch('disable-accelerated-video-encode');
app.commandLine.appendSwitch('disable-d3d11');
app.commandLine.appendSwitch('disable-dx11');
app.commandLine.appendSwitch('disable-features', 'VizDisplayCompositor');

// 禁用沙盒和安全策略以避免渲染限制
app.commandLine.appendSwitch('no-sandbox');
app.commandLine.appendSwitch('disable-setuid-sandbox');
app.commandLine.appendSwitch('ignore-gpu-blocklist');
app.commandLine.appendSwitch('in-process-gpu');
app.commandLine.appendSwitch('disable-gpu-driver-bug-workarounds');
app.commandLine.appendSwitch('disable-site-isolation-trials');
// 获取日志文件路径
function getLogFilePath() {
  // 日志文件放在用户数据目录中
  const logDir = path.join(app.getPath('userData'), 'logs');
  // 确保日志目录存在
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  // 生成带日期的日志文件名
  const date = new Date();
  const dateStr = `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`;
  return path.join(logDir, `app_${dateStr}.log`);
}

// 初始化日志文件
function initializeLogFile() {
  try {
    const logFilePath = getLogFilePath();
    
    // 使用 appendFile 而不是 openSync，避免文件句柄占用问题
    const initMessage = `${new Date().toISOString()} [INFO] 应用启动，日志系统初始化\n`;
    fs.appendFileSync(logFilePath, initMessage);
    
    // 输出到控制台，在开发模式可见
    const originalConsoleLog = console.log;
    const originalConsoleError = console.error;
    
    // 重写console.log，同时输出到控制台和日志文件
    console.log = function(...args) {
      const timestamp = new Date().toISOString();
      const logMessage = `${timestamp} [INFO] ${args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : arg
      ).join(' ')}\n`;
      
      // 保留原始控制台输出
      originalConsoleLog.apply(console, args);
      
      // 写入日志文件
      try {
        fs.appendFileSync(logFilePath, logMessage);
      } catch (writeError) {
        // 如果写入失败，至少保证控制台有输出
        originalConsoleError('写入日志文件失败:', writeError);
      }
    };
    
    // 重写console.error，同时输出到控制台和日志文件
    console.error = function(...args) {
      const timestamp = new Date().toISOString();
      const logMessage = `${timestamp} [ERROR] ${args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : arg
      ).join(' ')}\n`;
      
      // 保留原始控制台输出
      originalConsoleError.apply(console, args);
      
      // 写入日志文件
      try {
        fs.appendFileSync(logFilePath, logMessage);
      } catch (writeError) {
        // 如果写入失败，至少保证控制台有输出
        originalConsoleError('写入日志文件失败:', writeError);
      }
    };
    
    // 添加警告级别的日志
    console.warn = function(...args) {
      const timestamp = new Date().toISOString();
      const logMessage = `${timestamp} [WARN] ${args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : arg
      ).join(' ')}\n`;
      
      // 使用原始console.warn或降级到console.log
      if (originalConsoleLog.warn) {
        originalConsoleLog.warn.apply(console, args);
      } else {
        originalConsoleLog.apply(console, args);
      }
      
      // 写入日志文件
      try {
        fs.appendFileSync(logFilePath, logMessage);
      } catch (writeError) {
        originalConsoleError('写入日志文件失败:', writeError);
      }
    };
    
    console.log(`日志文件已初始化: ${logFilePath}`);
    return logFilePath;
  } catch (error) {
    // 使用基本的console输出，避免递归调用
    const basicLog = console._log || console.log;
    basicLog(`初始化日志文件失败: ${error.message}`);
    return null;
  }
}

// 确保在 app 准备好后再初始化日志文件
let logFilePath = null;

// 延迟初始化日志文件，确保 app 模块已完全初始化
function initializeLogsWhenReady() {
  if (app.isReady()) {
    logFilePath = initializeLogFile();
  } else {
    app.on('ready', () => {
      logFilePath = initializeLogFile();
    });
  }
}

// 调用延迟初始化函数
initializeLogsWhenReady();

let pyProc = null;
const PY_PORT = 5001;
const PY_HOST = '127.0.0.1';

function startBackend() {
  try {
    // 检测是否在asar归档中运行，如果是则使用解压后的路径
    let pyPath, scriptPath, cwd;
    
    // 检查__dirname是否包含asar
    if (__dirname.includes('app.asar')) {
      // 在asar环境中，使用resources目录下解压的文件
      const resourcesPath = process.resourcesPath;
      pyPath = path.join(resourcesPath, 'python-embed', 'python.exe');
      scriptPath = path.join(resourcesPath, 'backend', 'main.py');
      cwd = path.join(resourcesPath, 'backend');
      console.log(`在asar环境中，使用解压后的路径: ${pyPath}`);
    } else {
      // 在开发环境或未打包环境中，使用正常路径
      pyPath = path.join(__dirname, 'python-embed/python.exe');
      scriptPath = path.join(__dirname, 'backend/main.py');
      cwd = path.dirname(scriptPath);
      console.log(`在开发环境中，使用正常路径: ${pyPath}`);
    }

    // 检查Python路径存在性，并尝试多种可能的路径
    let foundPyPath = null;
    const possiblePyPaths = [
      pyPath,  // 主要路径
      path.join(__dirname, 'python-embed/python.exe'),  // 备选1：本地目录
      path.join(process.resourcesPath, 'python-embed/python.exe')  // 备选2：resources目录
    ];
    
    // 尝试所有可能的Python路径
    for (const testPath of possiblePyPaths) {
      console.log(`检查Python路径: ${testPath}`);
      if (fs.existsSync(testPath)) {
        foundPyPath = testPath;
        console.log(`找到有效的Python路径: ${testPath}`);
        break;
      } else {
        console.warn(`Python路径不存在: ${testPath}`);
      }
    }
    
    if (!foundPyPath) {
      console.error(`无法找到Python解释器！请检查应用程序安装。`);
      return false;
    }
    
    pyPath = foundPyPath;
    
    // 检查脚本路径存在性
    if (!fs.existsSync(scriptPath)) {
      console.error(`后端脚本不存在: ${scriptPath}`);
      // 尝试备选脚本路径
      const altScriptPath = path.join(process.resourcesPath, 'backend/main.py');
      if (fs.existsSync(altScriptPath)) {
        console.log(`使用备选脚本路径: ${altScriptPath}`);
        scriptPath = altScriptPath;
      } else {
        console.error(`备选脚本路径也不存在: ${altScriptPath}`);
        return false;
      }
    }
    
    console.log(`最终使用的Python路径: ${pyPath}`);
    console.log(`最终使用的脚本路径: ${scriptPath}`);
    
    // 使用pipe模式，以便更好地控制进程通信
    pyProc = spawn(pyPath, [scriptPath], {
      cwd: cwd,
      stdio: 'pipe'
    });

    // 捕获 Python 进程的标准输出
    pyProc.stdout.on('data', (data) => {
      // 尝试将数据转换为UTF-8字符串，避免编码问题
      const output = data.toString('utf-8');
      console.log(`Python stdout: ${output}`);
    });

    // 捕获 Python 进程的错误输出
    pyProc.stderr.on('data', (data) => {
      // 尝试将错误数据转换为UTF-8字符串，避免编码问题
      const output = data.toString('utf-8');
      console.error(`Python stderr: ${output}`);
    });

    pyProc.on('error', (err) => {
      console.error('启动后端失败:', err);
      console.error(`错误详情: ${err.code}, 系统调用: ${err.syscall}`);
      console.error(`路径: ${err.path}`);
      if (err.spawnargs) {
        console.error(`参数: ${err.spawnargs.join(' ')}`);
      }
      
      // 显示友好错误信息给用户
      console.error(`\n==== 错误说明 ====`);
      console.error(`无法启动Python后端服务，这可能是由于以下原因之一:`);
      console.error(`1. Python解释器未正确安装或打包`);
      console.error(`2. 后端代码文件不存在或路径错误`);
      console.error(`3. 文件权限问题`);
      console.error(`请检查日志文件以获取更多详细信息。`);
      console.error(`=================\n`);
    });

    pyProc.on('exit', (code) => {
      console.log(`后端进程退出，退出代码: ${code}`);
      if (code !== 0 && code !== null) {
        console.warn(`后端进程异常退出，退出代码: ${code}`);
      }
    });
    
    return true; // 表示启动成功
  } catch (error) {
    console.error(`启动后端时发生异常:`, error);
    return false;
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    // 隐藏菜单栏
    // autoHideMenuBar: true,
    // 或者使用 menuBarVisible: false 完全隐藏菜单栏
    // menuBarVisible: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true
    },
  });
  // 完全移除菜单
  Menu.setApplicationMenu(null); // 全局移除（影响所有窗口）
  // 等待后端启动后再加载前端（可选加健康检查）
  setTimeout(() => {
    win.loadFile('front/index.html'); // 假设 Vue 构建到 dist/
    // 生产环境建议注释掉这行，避免自动打开开发者工具
    // win.webContents.openDevTools()
  }, 2000);
}

app.whenReady().then(() => {
  console.log('应用已启动');
  console.log(`应用数据目录: ${app.getPath('userData')}`);
  
  startBackend();
  createWindow();

  app.on('activate', () => {
    console.log('应用已激活');
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// 捕获未处理的异常
process.on('uncaughtException', (error) => {
  console.error(`未捕获的异常: ${error.message}\n${error.stack}`);
});

// 捕获未处理的 Promise 拒绝
process.on('unhandledRejection', (reason, promise) => {
  console.error(`未处理的 Promise 拒绝: ${reason}`);
});

app.on('will-quit', () => {
  if (pyProc) {
    try {
      // 尝试发送SIGTERM信号（优雅终止）
      pyProc.kill('SIGTERM');
      console.log('已向Python进程发送SIGTERM信号');
      
      // 如果在Windows系统上，尝试使用taskkill命令彻底清理所有相关进程
      if (process.platform === 'win32') {
        const { execSync } = require('child_process');
        try {
          // 杀死所有与python-embed/python.exe相关的进程
          execSync('taskkill /F /IM python.exe /T', { stdio: 'ignore' });
          console.log('已使用taskkill清理所有Python进程');
        } catch (error) {
          // taskkill命令失败时不抛出异常，仅记录日志
          console.warn('taskkill命令执行失败，可能没有相关进程:', error.message);
        }
      }
    } catch (error) {
      console.error('关闭Python进程时发生错误:', error);
      // 尝试强制终止
      try {
        pyProc.kill('SIGKILL');
        console.log('已向Python进程发送SIGKILL信号');
      } catch (killError) {
        console.error('强制关闭Python进程时发生错误:', killError);
      }
    }
    pyProc = null;
  }
});