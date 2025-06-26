@echo off
chcp 936 >nul
setlocal enabledelayedexpansion

rem Git????? - ???????

rem ????
set REMOTE1_URL=https://github.com/the-man-in-a-case/mission-django.git
set REMOTE1_BRANCH=main
set REMOTE2_URL=git@192.168.119.200:222/Simulation/taskmanagementplatform.git
set REMOTE2_BRANCH=develop

rem ???Git?????
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo ??: ??????Git??!
    exit /b 1
)

rem ??????
echo ????????...
git remote | findstr /r /c:"^origin$" >nul
if errorlevel 1 (
    git remote add origin "!REMOTE1_URL!"
)
git remote | findstr /r /c:"^secondary$" >nul
if errorlevel 1 (
    git remote add secondary "!REMOTE2_URL!"
)

rem ??????
echo ????????:
git remote -v

rem ??????
set CONFIG_FILE=.git-multi-repo-config
(   echo REMOTE1_URL=!REMOTE1_URL!
    echo REMOTE1_BRANCH=!REMOTE1_BRANCH!
    echo REMOTE2_URL=!REMOTE2_URL!
    echo REMOTE2_BRANCH=!REMOTE2_BRANCH!
) > "!CONFIG_FILE!"
echo ???????? !CONFIG_FILE!
echo ???????????? git-sync.bat ????????????
endlocal