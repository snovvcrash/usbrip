FROM ubuntu
LABEL maintainer="snovvcrash@protonmail.ch"
ENV LANG="C.UTF-8"
RUN apt update && apt install python3 python3-venv -y
COPY . /src
WORKDIR /src
RUN python3 gen-demo-syslog.py && bash installers/install.sh && rm -rf /var/opt/usbrip
ENTRYPOINT ["usbrip"]
