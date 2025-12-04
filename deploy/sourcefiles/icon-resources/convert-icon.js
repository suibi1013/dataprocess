// 转换SVG为ICO格式的脚本
const fs = require('fs');
const path = require('path');

// 检查并安装依赖
const installDependencies = () => {
  const { execSync } = require('child_process');
  try {
    // 检查所需依赖是否已安装
    require('sharp');
    require('to-ico');
    console.log('所有依赖已经安装');
  } catch (error) {
    console.log('安装所需库...');
    execSync('npm install sharp to-ico', { stdio: 'inherit' });
  }
};

// 安装依赖
installDependencies();

// 引入所需库
const sharp = require('sharp');
const toIco = require('to-ico');

// SVG转PNG
async function svgToPng() {
  const svgPath = path.join(__dirname, 'icon.svg');
  const pngPath = path.join(__dirname, 'icon.png');
  
  try {
    await sharp(svgPath)
      .resize(256, 256)
      .png({ quality: 100 })
      .toFile(pngPath);
    
    console.log('SVG成功转换为PNG:', pngPath);
    return pngPath;
  } catch (error) {
    console.error('SVG转PNG失败:', error.message);
    return null;
  }
}

// PNG转ICO
async function pngToIco(pngPath) {
  const icoPath = path.join(__dirname, 'icon.ico');
  
  try {
    // 读取PNG文件
    const buffer = await sharp(pngPath)
      .resize(256, 256)
      .toBuffer();
    
    // 转换为ICO格式
    const icoBuffer = await toIco([buffer], {
      resize: true,
      sizes: [256, 128, 64, 32, 16] // 生成多种尺寸的图标
    });
    
    // 写入ICO文件
    fs.writeFileSync(icoPath, icoBuffer);
    
    console.log('PNG成功转换为ICO:', icoPath);
    return true;
  } catch (error) {
    console.error('PNG转ICO失败:', error.message);
    return false;
  }
}

// 创建说明文件
function createNotesFile() {
  const notesPath = path.join(__dirname, 'icon-notes.txt');
  const notesContent = `图标文件说明
===========

此目录包含以下图标文件：
- icon.svg: 矢量图原始文件（推荐编辑此文件）
- icon.png: 转换后的位图文件 (256x256)
- icon.ico: Windows应用图标文件（使用to-ico库生成的标准ICO格式）

注意事项：
- 如需修改图标，请编辑icon.svg文件
- 修改后运行此脚本重新生成PNG和ICO文件
- Windows应用打包时会使用icon.ico作为应用图标
`;
  
  try {
    fs.writeFileSync(notesPath, notesContent);
    console.log('说明文件已创建:', notesPath);
  } catch (error) {
    console.error('创建说明文件失败:', error.message);
  }
}

// 主函数
async function main() {
  console.log('开始转换图标...');
  
  // 转换SVG到PNG
  const pngPath = await svgToPng();
  if (!pngPath) {
    console.error('转换失败，退出脚本');
    process.exit(1);
  }
  
  // 转换PNG到ICO
  const icoResult = await pngToIco(pngPath);
  if (!icoResult) {
    console.error('ICO生成失败，退出脚本');
    process.exit(1);
  }
  
  // 创建说明文件
  createNotesFile();
  
  console.log('图标转换完成！');
}

// 运行主函数
main().catch(error => {
  console.error('脚本执行失败:', error);
  process.exit(1);
});