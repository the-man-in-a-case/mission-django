@echo off
setlocal enabledelayedexpansion

rem Git多仓库同步 - 操作脚本

rem 加载配置
set CONFIG_FILE=.git-multi-repo-config
if not exist "!CONFIG_FILE!" (
    echo 错误: 未找到配置文件！请先运行 git-setup.bat 进行初始化。
    exit /b 1
)
for /f "usebackq delims=" %%i in ("!CONFIG_FILE!") do set %%i

rem 确保在Git仓库目录内
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo 错误: 当前目录不是Git仓库!
    exit /b 1
)

rem 获取当前分支名称
for /f "delims=" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
echo 当前分支: !CURRENT_BRANCH!

rem 推送功能
:push_changes
    echo 开始推送更改...

    rem 检查是否有未提交的更改
git status --porcelain >nul 2>&1
if not errorlevel 1 (
    echo 检测到未提交的更改

    rem 获取commit信息
    if "%~1"=="" (
        set /p COMMIT_MSG=请输入commit信息: 
        if "!COMMIT_MSG!"=="" (
            set COMMIT_MSG=Auto commit by sync script !date! !time!
        )
    ) else (
        set COMMIT_MSG=%~1
    )

    rem 提交更改
echo 正在提交更改: !COMMIT_MSG!
git add .
git commit -m "!COMMIT_MSG!"
) else (
    echo 没有需要提交的更改
)

    rem 推送到第一个仓库
echo 正在推送到 !REMOTE1_URL! 的 !REMOTE1_BRANCH! 分支...
git push origin "!CURRENT_BRANCH!:!REMOTE1_BRANCH!"
if errorlevel 1 (
    echo 推送至第一个仓库失败
    exit /b 1
)

    rem 推送到第二个仓库
echo 正在推送到 !REMOTE2_URL! 的 !REMOTE2_BRANCH! 分支...
git push secondary "!CURRENT_BRANCH!:!REMOTE2_BRANCH!"
if errorlevel 1 (
    echo 推送至第二个仓库失败
    exit /b 1
)
echo 所有推送操作已完成!
exit /b 0

rem 拉取功能
:pull_changes
echo 开始从 !REMOTE1_URL! 的 !REMOTE1_BRANCH! 分支拉取...
git fetch origin "!REMOTE1_BRANCH!"
if errorlevel 1 (
    echo 从第一个仓库拉取失败
    exit /b 1
)
git merge "origin/!REMOTE1_BRANCH!" -m "Merge remote-tracking branch 'origin/!REMOTE1_BRANCH!'"
if errorlevel 1 (
    echo 合并失败，请手动解决冲突
    exit /b 1
)
echo 拉取并合并完成!
exit /b 0

rem 主程序
if "%~1"=="push" (
    call :push_changes %~2
) else if "%~1"=="pull" (
    call :pull_changes
) else (
    echo 未知命令: %~1
echo 用法: %~0 [push|pull] [commit信息]
exit /b 1
)
endlocal