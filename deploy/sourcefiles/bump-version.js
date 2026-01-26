// bump-version.js
const fs = require('fs');
const pkg = require('./package.json');

// 简单递增补丁版本（1.2.3 → 1.2.4）
const [major, minor, patch] = pkg.version.split('.').map(Number);
pkg.version = `${major}.${minor}.${patch + 1}`;

// 写回 package.json
fs.writeFileSync(
  'package.json',
  JSON.stringify(pkg, null, 2) + '\n',
  'utf8'
);

console.log(`✅ 版本已更新为: ${pkg.version}`);