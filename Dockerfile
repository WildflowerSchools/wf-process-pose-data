FROM ubuntu:20.04

RUN apt-get update

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get install -y python3 python3-pip apt-utils libgl1-mesa-glx libglib2.0-0

WORKDIR /wf-process-pose-data

COPY . .

RUN yes | pip3 install -r requirements.txt