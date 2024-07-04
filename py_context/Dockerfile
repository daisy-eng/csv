FROM python:latest            
RUN apt-get update && \       
    apt-get install -y \      
    build-essential \
    cmake \
    git \
    sudo \
    wget \
    vim
RUN pip install --upgrade pip                
COPY ./requirements.txt /requirements.txt    
RUN pip install -r /requirements.txt         
WORKDIR /work
CMD ["/bin/bash"] 