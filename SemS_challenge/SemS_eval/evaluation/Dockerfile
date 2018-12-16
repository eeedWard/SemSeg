#FROM python:2.7-alpine
FROM ubuntu:18.04

ARG CHALLENGE_EVALUATION=/challenge-evaluator

RUN apt-get update && apt-get install -y git python-pip

RUN echo CHALLENGE_EVALUATION=${CHALLENGE_EVALUATION}
RUN test -n "${CHALLENGE_EVALUATION}"
ENV CHALLENGE_EVALUATION ${CHALLENGE_EVALUATION}
ENV PYTHONPATH=/challenge-evaluator
COPY . ${CHALLENGE_EVALUATION}
COPY image ${CHALLENGE_EVALUATION}/image
COPY groundtruth ${CHALLENGE_EVALUATION}/groundtruth

RUN pip install -r ${CHALLENGE_EVALUATION}/requirements.txt

RUN chmod +x ${CHALLENGE_EVALUATION}/eval.py
CMD ${CHALLENGE_EVALUATION}/eval.py
