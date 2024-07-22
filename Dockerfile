# Dockerfile
# without an file extension

# Use an official Python runtime as a parent image
#FROM alkaline2018/python-slim-vim:0.0.2
FROM python:3.7.17-slim
LABEL authors="song"

# Set the working directory to /app
WORKDIR /app

#RUN apt-get -y install wget
#RUN wget https://dl.google.com/linux/linux_signing_key.pub
#RUN apt-get -y install gnupg && apt-key add linux_signing_key.pub
RUN apt-get -y update && apt-get -y upgrade

RUN pip install --upgrade pip
RUN apt-get install -y vim

# copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt
#RUN pip install --trusted-host file_transfer.daumkakao.com -r requirements.txt
# Copy the current directory contents into the container at /app

COPY . /app
ENV PYTHONPATH "${PYTHONPATH}:/"
# FIX: 실 배포시에는 prod로 변경 할 것
ENV APP_ENV "prod"