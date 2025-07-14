#!/bin/bash

# Git多仓库同步 - 初始化配置脚本

# 配置信息
REMOTE1_URL="https://github.com/the-man-in-a-case/mission-django.git"
REMOTE1_BRANCH="main"
REMOTE2_URL="git@192.168.119.200:222/Simulation/taskmanagementplatform.git"
REMOTE2_BRANCH="develop"

# 确保在Git仓库目录内
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "错误: 当前目录不是Git仓库!"
    exit 1
fi

# 添加远程仓库
echo "正在配置远程仓库..."
git remote | grep -q "origin" || git remote add origin "$REMOTE1_URL"
git remote | grep -q "secondary" || git remote add secondary "$REMOTE2_URL"

# 显示配置结果
echo "远程仓库配置完成:"
git remote -v

# 创建配置文件
CONFIG_FILE=".git-multi-repo-config"
cat > "$CONFIG_FILE" <<EOF
REMOTE1_URL="$REMOTE1_URL"
REMOTE1_BRANCH="$REMOTE1_BRANCH"
REMOTE2_URL="$REMOTE2_URL"
REMOTE2_BRANCH="$REMOTE2_BRANCH"
EOF

echo "配置文件已保存到 $CONFIG_FILE"
echo "初始化完成！现在可以使用 git-sync.sh 脚本进行推送和拉取操作。"    