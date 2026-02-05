// 系统版本更新记录
// 技术人员可以在此文件中添加或修改版本更新记录
export interface VersionInfo {
  version: string;
  date: string;
  changes: string[];
}

export const versionHistory: VersionInfo[] = [
  {
    version: '1.2.0',
    date: '2026-02-01',
    changes: [
      '新增系统版本更新记录功能',
      '优化数据备份与还原功能',
      '修复部分浏览器兼容性问题',
      '提升系统整体性能'
    ]
  },
  {
    version: '1.1.0',
    date: '2026-01-15',
    changes: [
      '添加数据备份与还原功能',
      '优化用户界面布局',
      '增加系统信息展示',
      '修复已知bug'
    ]
  },
  {
    version: '1.0.0',
    date: '2026-01-01',
    changes: [
      '系统正式发布',
      '实现核心功能',
      '支持数据源管理，仅支持excel类型',
      '添加模板管理功能，部分功能未实现'
    ]
  }
];
