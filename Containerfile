FROM docker.io/cm2network/steamcmd:root
LABEL maintainer="wh2099@outlook.com"

USER root
WORKDIR /
VOLUME ["mods", "/ugc", "/install", "/cluster"]

# 更新 steamcmd
RUN chmod u+w / && \
    cp -r /home/steam/steamcmd ./ && \
    ./steamcmd/steamcmd.sh +quit

ARG DST_64_PKGS="libcurl3-gnutls procps"
RUN apt-get update && \
    apt-get install -y ${DST_64_PKGS} iproute2 && \
    apt-get -y clean

# 入口脚本
COPY entrypoint.sh .
CMD ["/usr/bin/bash", "/entrypoint.sh"]