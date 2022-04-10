FROM cm2network/steamcmd:root
LABEL maintainer="wh2099@outlook.com"

# 64 位服务端依赖
RUN apt-get update\
    && apt-get install -y libcurl3-gnutls\
    && apt-get clean autoclean

# 持久数据卷
VOLUME [ "/data/conf" ]

# 入口脚本
COPY --chown=steam:steam ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


USER steam:steam
ENTRYPOINT ["/entrypoint.sh"]