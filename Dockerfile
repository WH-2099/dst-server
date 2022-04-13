FROM cm2network/steamcmd:root
LABEL maintainer="wh2099@outlook.com"

# 持久数据卷
# steam:steam 实际为 1000:1000
# 与一般情况下外部系统中首个普通用户的 UID:GID 一致
VOLUME [ "/data/conf" ]
RUN chown -R steam:steam /data

# 入口脚本
COPY --chown=steam:steam ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 64 位服务端依赖
RUN apt-get update \
    && apt-get install -y libcurl3-gnutls procps \
    && apt-get clean autoclean

# 容器内外环境权限易冲突，保持 root 运行
# USER steam:steam
ENTRYPOINT ["/entrypoint.sh"]