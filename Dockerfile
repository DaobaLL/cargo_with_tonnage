# 使用更完整的基础镜像
FROM debian:bullseye

# 安装必要的工具
RUN apt-get update && apt-get install -y wget tar python3 python3-pip && \
    wget -qO /tmp/mongo-tools.tgz https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian11-x86_64-100.7.0.tgz && \
    tar -xvzf /tmp/mongo-tools.tgz -C /usr/local/bin --strip-components=1 && \
    rm -rf /tmp/mongo-tools.tgz

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY . /app

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 暴露 Flask 默认端口
EXPOSE 5000

# 设置启动命令
CMD ["python3", "main.py"]