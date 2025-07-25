#!/bin/bash

# GROBID Docker服务设置和测试脚本

set -e

echo "🚀 GROBID Docker服务设置脚本"
echo "=" * 50

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

echo "✅ Docker已安装"

# 检查是否已有GROBID容器在运行
EXISTING_CONTAINER=$(docker ps --filter "ancestor=grobid/grobid:0.8.2" --format "{{.ID}}" | head -1)

if [ ! -z "$EXISTING_CONTAINER" ]; then
    echo "⚠️ 发现已运行的GROBID容器: $EXISTING_CONTAINER"
    echo "是否要停止现有容器并重新启动？(y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🛑 停止现有容器..."
        docker stop $EXISTING_CONTAINER
    else
        echo "ℹ️ 保持现有容器运行"
        exit 0
    fi
fi

# 拉取GROBID Docker镜像
echo "📥 拉取GROBID Docker镜像..."
docker pull grobid/grobid:0.8.2

# 启动GROBID容器
echo "🚀 启动GROBID容器..."
docker run -d \
    --name grobid-service \
    --rm \
    --init \
    --ulimit core=0 \
    -p 8070:8070 \
    -p 8071:8071 \
    grobid/grobid:0.8.2

echo "⏳ 等待GROBID服务启动..."
sleep 10

# 测试GROBID服务
echo "🧪 测试GROBID服务..."

# 检查服务是否存活
echo "检查服务状态..."
if curl -s http://localhost:8070/api/isalive | grep -q "true"; then
    echo "✅ GROBID服务运行正常"
else
    echo "❌ GROBID服务未正常启动"
    echo "查看容器日志："
    docker logs grobid-service
    exit 1
fi

# 获取版本信息
echo "📋 GROBID版本信息："
curl -s http://localhost:8070/api/version

echo ""
echo "🎉 GROBID服务设置完成！"
echo ""
echo "📍 服务地址："
echo "  - Web界面: http://localhost:8070"
echo "  - 健康检查: http://localhost:8071"
echo "  - API文档: http://localhost:8070/api/"
echo ""
echo "🛑 停止服务命令："
echo "  docker stop grobid-service"
echo ""
echo "📊 查看服务状态："
echo "  docker ps --filter name=grobid-service"
echo ""
echo "📝 查看服务日志："
echo "  docker logs grobid-service"
