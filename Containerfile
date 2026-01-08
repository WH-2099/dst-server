FROM docker.io/cm2network/steamcmd:root
LABEL maintainer="wh2099@pm.me"

ARG BETA=""
ARG DST_64_PKGS="libcurl3-gnutls procps"

WORKDIR /
VOLUME ["/cluster"]

# 安装 DST 服务端依赖
RUN apt-get update && \
    apt-get install -y ${DST_64_PKGS} && \
    apt-get -y clean

# 安装 DST 服务端
RUN chmod u+w / && \
    chown -R root:root ${STEAMCMDDIR} && \
    ${STEAMCMDDIR}/steamcmd.sh +force_install_dir /install +login anonymous +app_update 343050 ${BETA:+ -beta updatebeta} validate +quit

# 入口脚本
COPY entrypoint.sh .
CMD ["/usr/bin/bash", "/entrypoint.sh"]
