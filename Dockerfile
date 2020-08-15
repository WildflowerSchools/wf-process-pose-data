FROM ubuntu:20.04

RUN apt-get update

RUN apt-get install -y python3 python3-pip apt-utils

RUN pip3 install wf-pose-tracking-3d>=0.1.0

RUN pip3 install wf-smc-kalman>-0.1.0

RUN pip3 install wf-cv-utils>=0.5.1

RUN pip3 install wf-video-io>=0.1.0

RUN pip3 install wf-minimal-honeycomb-python>=0.5.0

RUN pip3 install wf-geom-render>=0.3.0

RUN pip3 install pandas>=0.25.3

RUN pip3 install numpy>=1.18.1

RUN pip3 install networkx>=2.4

RUN pip3 install tqdm>=4.42.0

RUN pip3 install opencv-python>=4.2.0.34

RUN pip3 install python-slugify>=4.0.0

RUN pip3 install matplotlib>=3.1.2

RUN pip3 install seaborn>=0.10.0

WORKDIR /wf-process-pose-data

COPY . .

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get install -y libgl1-mesa-glx libglib2.0-0

RUN pip3 install attrs
