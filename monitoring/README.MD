# GPU Monitoring Guide

## Pre-reqs

- Install DCGM driver
```
#!/bin/bash

distribution=$(. /etc/os-release;echo $ID$VERSION_ID | sed -e 's/\.//g')
echo "deb http://developer.download.nvidia.com/compute/cuda/repos/$distribution/x86_64 /" | sudo tee /etc/apt/sources.list.d/cuda.list 
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/$distribution/x86_64/7fa2af80.pub
wget https://developer.download.nvidia.com/compute/cuda/repos/$distribution/x86_64/cuda-$distribution.pin
sudo mv cuda-$distribution.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-get update
sudo apt-get install -y datacenter-gpu-manager
# Enable DCGM systemd service (on reboot) and start it now
sudo systemctl --now enable nvidia-dcgm

```

## Dashboard commands

1. Create dashboard from Cloud Monitoring UI
2. Get Dashboard ID from the URL
3. Use the describe command to get the etag, and add the etag to the dashboard.json
4. Update the dashboard

```
DASHBOARD_ID=abc123
```

**Describe dashboard**
```
gcloud monitoring dashboards describe $DASHBOARD_ID
```

**Update dashboard**
- Add etag from dashboard describe
```
gcloud monitoring dashboards update $DASHBOARD_ID --config-from-file=dashboard.json
```

## Running and building the image

```
export PROJECT_ID=your_proj
export IMAGE_NAME=monitoring-image
```

**Build**
```
docker build -t $IMAGE_NAME .
```

**Run**
```
docker run --rm --network host monitoring-image --project_id kz-2021-267823
```

