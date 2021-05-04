FROM python:2.7.18-buster
WORKDIR /source
RUN apt-get update \ 
    && apt-get install -y software-properties-common \
    && wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin \
    && mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600 \
    && apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub \
    && add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /" \
    && apt-get update \
    && apt-get install -y datacenter-gpu-manager
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY dcgm_stackdriver.py .
ENV PYTHONPATH=/usr/local/dcgm/bindings
ENTRYPOINT ["python2", "dcgm_stackdriver.py"]
