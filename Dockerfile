FROM cm2network/steamcmd:root
LABEL maintainer="wh2099@outlook.com"

USER root
WORKDIR /root
VOLUME ["/ugc", "/mods" ,"/install", "/cluster"]

# 更新 steamcmd
RUN chmod u+w / && \
    cp -r /home/steam/steamcmd ./ && \
    ./steamcmd/steamcmd.sh +quit

ARG DST_64_PKGS="libcurl3-gnutls procps"
RUN apt-get update && \
    apt-get install -y ${DST_64_PKGS}

# ARG PYTHON_VERSION="3.11.4"
# ARG PYTHON_BUILD_PKGS="build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev libbz2-dev"
# RUN apt-get install -y  ${PYTHON_BUILD_PKGS} && \
#     curl -fsSL https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz | tar -xz && \
#     cd Python-${PYTHON_VERSION} && \
#     ./configure --enable-optimizations && \
#     make -j $(nproc) && \
#     make install
# RUN apt-get -y clean && \ 
#     rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* Python-${PYTHON_VERSION}

# 入口脚本
COPY ./entrypoint.sh ./entrypoint.py ./
ENTRYPOINT ["/bin/bash"]
CMD ["./entrypoint.sh"]
# CMD ["./entrypoint.py"]