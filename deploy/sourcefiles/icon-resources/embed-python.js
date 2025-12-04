const fs = require('fs');
const path = require('path');
const { execSync, exec } = require('child_process');
const https = require('https');
const unzipper = require('unzipper');
const rimraf = require('rimraf');

// 嵌入式Python配置
const PYTHON_VERSION = '3.9.13'; // 使用较稳定的Python 3.9版本
const PYTHON_ARCH = 'amd64'; // 64位版本
const PYTHON_URL = `https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-embed-${PYTHON_ARCH}.zip`;
const PYTHON_DIR = path.join(__dirname, '../python-embedded');
const PYTHON_EXE = path.join(PYTHON_DIR, 'python.exe');
const PIP_BOOTSTRAP_URL = 'https://bootstrap.pypa.io/get-pip.py';

// 清理已存在的Python环境
function cleanup() {
  console.log('清理已存在的Python环境...');
  if (fs.existsSync(PYTHON_DIR)) {
    rimraf.sync(PYTHON_DIR);
  }
  fs.mkdirSync(PYTHON_DIR, { recursive: true });
}

// 下载文件
function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    console.log(`下载文件: ${url} -> ${dest}`);
    const file = fs.createWriteStream(dest);
    https.get(url, response => {
      response.pipe(file);
      file.on('finish', () => {
        file.close();
        console.log(`下载完成: ${dest}`);
        resolve(dest);
      });
    }).on('error', err => {
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

// 解压ZIP文件
function extractZip(zipPath, destDir) {
  return new Promise((resolve, reject) => {
    console.log(`解压文件: ${zipPath} -> ${destDir}`);
    fs.createReadStream(zipPath)
      .pipe(unzipper.Extract({ path: destDir }))
      .on('close', () => {
        console.log(`解压完成: ${destDir}`);
        resolve();
      })
      .on('error', reject);
  });
}

// 安装pip
async function installPip() {
  console.log('安装pip...');
  const getPipPath = path.join(PYTHON_DIR, 'get-pip.py');
  await downloadFile(PIP_BOOTSTRAP_URL, getPipPath);
  
  // 修改python39._pth文件以允许导入site-packages
  const pthFilePath = path.join(PYTHON_DIR, 'python39._pth');
  if (fs.existsSync(pthFilePath)) {
    let content = fs.readFileSync(pthFilePath, 'utf8');
    // 移除#以启用site-packages
    content = content.replace(/#import site/, 'import site');
    fs.writeFileSync(pthFilePath, content);
  }
  
  // 运行get-pip.py安装pip
  execSync(`"${PYTHON_EXE}" "${getPipPath}"`, { stdio: 'inherit', cwd: PYTHON_DIR });
  console.log('pip安装完成');
}

// 安装项目依赖
async function installDependencies() {
  console.log('安装项目依赖...');
  const requirementsPath = path.join(__dirname, '../api/requirements.txt');
  if (fs.existsSync(requirementsPath)) {
    const pipPath = path.join(PYTHON_DIR, 'Scripts', 'pip.exe');
    execSync(`"${pipPath}" install -r "${requirementsPath}"`, { stdio: 'inherit', cwd: PYTHON_DIR });
    console.log('依赖安装完成');
  } else {
    console.log('未找到requirements.txt文件');
  }
}

// 主函数
async function main() {
  try {
    // 检查并安装所需的Node.js依赖
    console.log('检查并安装Node.js依赖...');
    try {
      require('unzipper');
      require('rimraf');
    } catch (error) {
      console.log('安装Node.js依赖...');
      execSync('npm install unzipper rimraf', { stdio: 'inherit' });
    }
    
    // 清理已存在的Python环境
    cleanup();
    
    // 下载并解压Python
    const zipPath = path.join(__dirname, 'python-embedded.zip');
    await downloadFile(PYTHON_URL, zipPath);
    await extractZip(zipPath, PYTHON_DIR);
    
    // 删除下载的ZIP文件
    fs.unlinkSync(zipPath);
    
    // 安装pip
    await installPip();
    
    // 安装项目依赖
    await installDependencies();
    
    console.log('嵌入式Python环境准备完成！');
    console.log(`Python可执行文件路径: ${PYTHON_EXE}`);
    
    // 创建README文件
    const readmeContent = `嵌入式Python环境
================

此目录包含嵌入式Python环境，用于PPT转HTML工具应用。

版本信息：
- Python: ${PYTHON_VERSION} (${PYTHON_ARCH})

注意事项：
- 请勿手动修改此目录下的文件
- 此环境仅用于PPT转HTML工具应用
- 如果需要更新Python版本或依赖，请重新运行embed-python.js脚本
`;
    fs.writeFileSync(path.join(PYTHON_DIR, 'README.txt'), readmeContent);
    
  } catch (error) {
    console.error('错误:', error);
    process.exit(1);
  }
}

// 运行主函数
main();