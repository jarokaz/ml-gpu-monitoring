---
title: Fine-tuning a BERT model on A2 VM
description: This guide demonstrates how to fine-tune a BERT model from TensorFlow Model Garden on a GCP A2 Deep Learning VM instance.
author: jarokaz
tags: NLP, DL, ML, Cloud Monitoring, DCGM
date_published: 2020-04-28
---

Jarek Kazmierczak | Solutions Architect | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

... work in progress

This guide walks you through the process of fine-tuning a large BERT model from [TensorFlow Model Garden](https://github.com/tensorflow/models) on a multi-gpu Deep Learning GCE A2 VM instance. 

## Objectives

*   Provision an GCE A2 VM instance using a Deep Learning VM image
*   Configure a distributed training regimen for fine tuning a large BERT model using [TensorFlow NLP Modelling Toolkit](https://github.com/tensorflow/models/tree/master/official/nlp) 
*   Configure GPU monitoring using [NVidia Data Center GPU Manager](https://developer.nvidia.com/dcgm) and [Cloud Monitoring](https://cloud.google.com/monitoring)
*   Execute and monitor a fine tuning job

## Costs

This tutorial uses billable components of Google Cloud, including the following:

*   [GCE A2 instance](https://cloud.google.com/compute/docs/gpus)
*   [Cloud Monitoring](https://cloud.google.com/monitoring)
*   [Cloud Storage](https://cloud.google.com/storage)

Use the [pricing calculator](https://cloud.google.com/products/calculator) to generate a cost estimate based on your projected usage.

## Before you begin

TBD

## Understanding the fine tuning process

TBD

## Provisioning an A2 GCE instance

... work in progress

```
PROJECT_ID=jk-mlops-dev
ZONE= us-central1-c
INSTANCE_NAME=jk-a2-1g
MACHINE_TYPE=a2-highgpu-1g
IMAGE_FAMILY=common-cu110


gcloud compute instances create $INSTANCE_NAME \
   --project $PROJECT_ID \
   --zone $ZONE \
   --machine-type $MACHINE_TYPE \
   --maintenance-policy TERMINATE --restart-on-failure \
   --image-family $IMAGE_FAMILY \
   --image-project deeplearning-platform-release \
   --boot-disk-size 200GB \
   --metadata "install-nvidia-driver=True,proxy-mode=project_editors" \
   --metadata-from-file startup-script=install-dcgm.sh \
   --scopes https://www.googleapis.com/auth/cloud-platform
```

## Configuring GPU monitoring

... work in progress

## Preparing MNLI dataset

Download and unzip the MNLI dataset

```
MNLI_ZIP_URL=https://dl.fbaipublicfiles.com/glue/data/MNLI.zip
MNLI_LOCAL_FOLDER=/tmp

curl -o $MNLI_LOCAL_FOLDER/MNLI.zip $MNLI_ZIP_URL
unzip $MNLI_LOCAL_FOLDER/MNLI.zip -d $MNLI_LOCAL_FOLDER
```

Create TF record files

```
OUTPUT_DIR=gs://jk-bert-lab-bucket/datasets

docker run -it --rm --gpus all \
--volume ${MNLI_LOCAL_FOLDER}/MNLI:/data/MNLI \
--env OUTPUT_DIR=${OUTPUT_DIR} \
--env TASK=MNLI \
--env BERT_DIR=gs://cloud-tpu-checkpoints/bert/keras_bert/uncased_L-24_H-1024_A-16 \
gcr.io/jk-mlops-dev/models-official \
'python models/official/nlp/data/create_finetuning_data.py \
 --input_data_dir=/data/MNLI \
 --vocab_file=${BERT_DIR}/vocab.txt \
 --train_data_output_path=${OUTPUT_DIR}/${TASK}/${TASK}_train.tf_record \
 --eval_data_output_path=${OUTPUT_DIR}/${TASK}/${TASK}_eval.tf_record \
 --meta_data_file_path=${OUTPUT_DIR}/${TASK}/${TASK}_meta_data \
 --fine_tuning_task_type=classification --max_seq_length=128 \
 --classification_task_name=${TASK}'
```

## Executing a training job

```
OUTPUT_DIR=gs://jk-bert-lab-bucket/models 

docker run -it --rm --gpus all \
--env OUTPUT_DIR=$OUTPUT_DIR \
--env TASK=MNLI \
--env DATA_DIR=gs://jk-bert-lab-bucket/datasets \
--env BERT_DIR=gs://cloud-tpu-checkpoints/bert/keras_bert/uncased_L-24_H-1024_A-16 \
gcr.io/jk-mlops-dev/models-official \
'python models/official/nlp/bert/run_classifier.py \
 --mode='train_and_eval' \
 --input_meta_data_path=${DATA_DIR}/${TASK}/${TASK}_meta_data \
 --train_data_path=${DATA_DIR}/${TASK}/${TASK}_train.tf_record \
 --eval_data_path=${DATA_DIR}/${TASK}/${TASK}_eval.tf_record \
 --bert_config_file=${BERT_DIR}/bert_config.json \
 --init_checkpoint=${BERT_DIR}/bert_model.ckpt \
 --train_batch_size=32 \
 --eval_batch_size=32 \
 --steps_per_loop=1 \
 --learning_rate=2e-5 \
 --num_train_epochs=3 \
 --model_dir=${OUTPUT_DIR}/${TASK} \
 --distribution_strategy=mirrored \
 --num_gpus=2'
```





## Monitoring a training job

## Cleaning up

To avoid incurring charges to your Google Cloud account for the resources used in this tutorial, you can delete the project.

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work that you've done in the project.
- You can't reuse the project ID of a deleted project. If you created a custom project ID that you plan to use in the
  future, delete the resources inside the project instead. This ensures that URLs that use the project ID, such as
  an `appspot.com` URL, remain available.

To delete a project, do the following:

1.  In the Cloud Console, go to the [Projects page](https://console.cloud.google.com/iam-admin/projects).
1.  In the project list, select the project you want to delete and click **Delete**.
1.  In the dialog, type the project ID, and then click **Shut down** to delete the project.

## What's next

TBD

## Scratchpad

```
VM_NAME=jk-a100-8
PROJECT_ID=jk-mlops-dev
ZONE=us-central1-c

gcloud compute instances create $VM_NAME \
   --project $PROJECT_ID \
   --zone $ZONE \
   --machine-type a2-highgpu-8g \
   --maintenance-policy TERMINATE --restart-on-failure \
   --image-family tf2-ent-2-3-cu110 \
   --image-project deeplearning-platform-release \
   --boot-disk-size 200GB \
   --metadata "install-nvidia-driver=True,proxy-mode=project_editors" \
   --network-interface=nic-type=GVNIC \
   --scopes https://www.googleapis.com/auth/cloud-platform
```

```
VM_NAME=jk-t4-4
PROJECT_ID=jk-mlops-dev
ZONE=us-west1-a

gcloud compute instances create $VM_NAME \
   --project $PROJECT_ID \
   --custom-cpu 96 \
   --custom-memory 624 \
   --image-project=deeplearning-platform-release \
   --image-family=tf-latest-gpu-gvnic \
   --accelerator type=nvidia-tesla-t4,count=4 \
   --maintenance-policy TERMINATE \
   --metadata="install-nvidia-driver=True"  \
   --boot-disk-size 200GB \
   --network-interface=nic-type=GVNIC \
   --zone=$ZONE
```

```
VM_NAME=jk-v100-1
PROJECT_ID=jk-mlops-dev
ZONE=us-west1-a

gcloud compute instances create $VM_NAME \
   --project $PROJECT_ID \
   --custom-cpu 12 \
   --custom-memory 78 \
   --image-project=deeplearning-platform-release \
   --image-family=tf-latest-gpu-gvnic \
   --accelerator type=nvidia-tesla-v100,count=1 \
   --maintenance-policy TERMINATE \
   --metadata="install-nvidia-driver=True"  \
   --boot-disk-size 200GB \
   --network-interface=nic-type=GVNIC \
   --zone=$ZONE
```

```
VM_NAME=jk-t4-1
PROJECT_ID=jk-mlops-dev
ZONE=us-west1-a

gcloud compute instances create $VM_NAME \
   --project $PROJECT_ID \
   --custom-cpu 24 \
   --custom-memory 156 \
   --image-project=deeplearning-platform-release \
   --image-family=tf-latest-gpu-gvnic \
   --accelerator type=nvidia-tesla-t4,count=1 \
   --maintenance-policy TERMINATE \
   --metadata="install-nvidia-driver=True"  \
   --boot-disk-size 200GB \
   --network-interface=nic-type=GVNIC \
   --zone=$ZONE
```
