FROM cm2network/steamcmd:root
LABEL maintainer="wh2099@outlook.com"
# 补充 64 位服务端依赖
RUN apt-get update\
    && apt-get install -y libcurl3-gnutls\
    && apt-get clean autoclean
# 设置持久数据卷
VOLUME [ "/data/conf" ]
# 复制入口脚本
COPY --chown=steam:steam ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 设置运行用户为 steam
USER steam:steam
ENTRYPOINT ["/entrypoint.sh"]
CMD ["Master"]