#!/bin/bash

# Git多仓库同步 - 操作脚本

# 加载配置
CONFIG_FILE=".git-multi-repo-config"
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "错误: 未找到配置文件！请先运行 git-setup.sh 进行初始化。"
    exit 1
fi

# 确保在Git仓库目录内
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "错误: 当前目录不是Git仓库!"
    exit 1
fi

# 获取当前分支名称
CURRENT_BRANCH=$(git branch --show-current)
echo "当前分支: $CURRENT_BRANCH"

# 推送功能
push_changes() {
    echo "开始推送更改..."
    
    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        echo "检测到未提交的更改"
        
        # 获取commit信息
        if [ -z "$1" ]; then
            read -p "请输入commit信息: " COMMIT_MSG
            if [ -z "$COMMIT_MSG" ]; then
                COMMIT_MSG="Auto commit by sync script $(date +'%Y-%m-%d %H:%M:%S')"
            fi
        else
            COMMIT_MSG="$1"
        fi
        
        # 提交更改
        echo "正在提交更改: $COMMIT_MSG"
        git add .
        git commit -m "$COMMIT_MSG"
    else
        echo "没有需要提交的更改"
    fi
    
    # 推送到第一个仓库
    echo "正在推送到 $REMOTE1_URL 的 $REMOTE1_BRANCH 分支..."
    git push origin "$CURRENT_BRANCH:$REMOTE1_BRANCH" || { echo "推送至第一个仓库失败"; return 1; }
    
    # 推送到第二个仓库
    echo "正在推送到 $REMOTE2_URL 的 $REMOTE2_BRANCH 分支..."
    git push secondary "$CURRENT_BRANCH:$REMOTE2_BRANCH" || { echo "推送至第二个仓库失败"; return 1; }
    
    echo "所有推送操作已完成!"
}

# 拉取功能
pull_changes() {
    echo "开始从 $REMOTE1_URL 的 $REMOTE1_BRANCH 分支拉取..."
    
    # 从第一个仓库拉取
    git fetch origin "$REMOTE1_BRANCH" || { echo "从第一个仓库拉取失败"; return 1; }
    
    # 合并到当前分支
    git merge "origin/$REMOTE1_BRANCH" -m "Merge remote-tracking branch 'origin/$REMOTE1_BRANCH'" || { 
        echo "合并失败，请手动解决冲突"
        return 1
    }
    
    echo "拉取并合并完成!"
}

# 主程序
case "$1" in
    push)
        push_changes "$2"
        ;;
    pull)
        pull_changes
        ;;
    *)
        echo "未知命令: $1"
        echo "用法: $0 [push|pull] [commit信息]"
        exit 1
        ;;
esac    