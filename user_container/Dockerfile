FROM python:3.9-slim

RUN apt-get update && apt-get install -y   gcc    python3-dev   supervisor    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制user_gateway的依赖（假设requirements.txt已生成）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 使用已有的supervisord.conf（用户提供的user_gateway/supervisord.conf）
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 暴露网关服务端口（根据实际配置调整）
EXPOSE 8000

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]