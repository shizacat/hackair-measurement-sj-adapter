FROM ubuntu:18.04
MAINTAINER a.matveev

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Moscow

COPY requirements.txt requirements.txt

RUN apt-get	update && \
	apt-get install -y --no-install-recommends \
		python3 python3-pip python3-idna python3-six python3-setuptools \
		locales git && \
	pip3 install --no-cache-dir -r requirements.txt && \
	apt-get -y autoremove && \
	rm -rf /var/lib/apt/lists/*

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

COPY ["./source/", "/opt/service/"]

WORKDIR	/opt/service

ENTRYPOINT ["/opt/service/service.py"]
CMD ["--help"]
