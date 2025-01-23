FROM docker.io/cm2network/steamcmd:root
LABEL maintainer="wh2099@outlook.com"

ARG DST_64_PKGS="libcurl3-gnutls procps"

USER root
WORKDIR /
VOLUME ["/install", "/cluster"]

# 安装 DST 服务端依赖
RUN apt-get update && \
    apt-get install -y ${DST_64_PKGS} && \
    apt-get -y clean

# 更新 steamcmd 并安装 DST 服务端
RUN chmod u+w / && \
    mv /home/steam/steamcmd / && \
    /steamcmd/steamcmd.sh +quit && \
    /steamcmd/steamcmd.sh +login anonymous +force_install_dir /install +app_update 343050 validate +quit

# 入口脚本
COPY entrypoint.sh .
CMD ["/usr/bin/bash", "/entrypoint.sh"]