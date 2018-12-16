FROM ubuntu:16.04

RUN apt-get update \
    && apt-get install -y wget \
    && wget https://www.princexml.com/download/prince_12.2-1_ubuntu16.04_amd64.deb \
    && apt-get install -y \
	git \
	python-pip \
	imagemagick \
	./prince_12.2-1_ubuntu16.04_amd64.deb \
    && apt-get remove -y wget
# sometimes I need 
#   && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y curl

WORKDIR /duckietown-challenges-server


# fix for imagemagick
COPY  fix.py .
RUN python fix.py && prince --version


# only redo this step if requirements change
COPY requirements.txt .
RUN pip install -r requirements.txt




COPY  . .

# install but no deps (we want them pinned by requirements.txt)
RUN  python setup.py develop --no-deps

CMD pserve /duckietown-challenges-server/deployment/duckietown-server-local.ini

HEALTHCHECK --interval=120s --timeout=60s CMD curl -f http://localhost:6545/ || exit 1

#HEALTHCHECK --interval=5s  --timeout=10s CMD curl -f http://localhost:6545/humans/users || exit 1
#HEALTHCHECK --interval=29s --timeout=10s CMD curl -f http://localhost:6545/humans/submissions || exit 1
#HEALTHCHECK --interval=28s --timeout=10s CMD curl -f http://localhost:6545/humans/jobs || exit 1
#HEALTHCHECK --interval=29s --timeout=10s CMD curl -f http://localhost:6545/humans/logs || exit 1
#HEALTHCHECK --interval=28s --timeout=10s CMD curl -f http://localhost:6545/humans/dashboard || exit 1
#HEALTHCHECK --interval=28s --timeout=10s CMD curl -f http://localhost:6545/jobs-by-submission/1 || exit 1

