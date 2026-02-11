!macro preInit
  SetShellVarContext all
  
  ; 创建或更新自定义日志文件示例代码
  ; StrCpy $2 "c:\setup_debug.log"
  ; FileOpen最后一个参数为打开模式，包括写入模式(w,文件不存在时，自动创建新文件；存在时清空原内容，再写入)，追加模式(a)，只读模式(r)
  ; FileOpen $3 "$2" w
  ; FileWrite $3 "=== 安装调试日志 ===$\r$\n"
  ; FileWrite $3 "APP_GUID: ${APP_GUID}$\r$\n"
  ; FileClose $3

  ; 先查 HKCU（当前用户）的 InstallLocation
  ReadRegStr $1 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "InstallLocation"
  StrCmp $1 "" 0 +3
    ; 再查 HKLM（所有用户）的 InstallLocation
    ReadRegStr $1 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "InstallLocation"
    StrCmp $1 "" no_backup
  
  ; 检查路径有效性
  StrCmp $1 "" no_backup
  IfFileExists "$1\resources\backend\database.db" 0 no_backup

  ; 备份到 TEMP
  CopyFiles "$1\resources\backend\database.db" "$TEMP\database.db.bak" 


no_backup:
!macroend

!macro customInstall
  ; 创建注册表项
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_GUID}" "InstallLocation" "$INSTDIR"
  ; 创建目录
  CreateDirectory "$INSTDIR\resources\backend"

  ; 恢复备份（如有）
  IfFileExists "$TEMP\database.db.bak" 0 +4
    CopyFiles "$TEMP\database.db.bak" "$INSTDIR\resources\backend\database.db"

  ; 执行更新脚本
  IfFileExists "$INSTDIR\resources\backend\build\update_database.py" 0 +5
    ExecWait '"$INSTDIR\python-embed\python.exe" "$INSTDIR\resources\backend\build\update_database.py"'
!macroend

!macro customHeader
  ; 自定义安装程序头部
!macroend

!macro customWelcome
  ; 自定义欢迎页面
!macroend

!macro customInstallMode
  ; 自定义安装模式页面
!macroend

!macro customDirectory
  ; 自定义目录选择页面
!macroend

!macro customComponents
  ; 自定义组件选择页面
!macroend

!macro customTasks
  ; 自定义任务页面
!macroend

!macro customInstFiles
  ; 自定义安装文件页面
!macroend

!macro customFinish
  ; 如果启用了日志，提示用户
!macroend

!macro customUnInstallMode
  ; 自定义卸载模式页面
!macroend

!macro customUnInstallConfirm
  ; 自定义卸载确认页面
!macroend

!macro customUnInstallFiles
  ; 自定义卸载文件页面
!macroend

!macro customUnInstallFinish
  ; 自定义卸载完成页面
!macroend