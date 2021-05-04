ARG TF_VERSION=2-4
FROM gcr.io/deeplearning-platform-release/tf2-gpu.$TF_VERSION
ARG MODELS_BRANCH=v2.4.0
WORKDIR /source
RUN git clone -b $MODELS_BRANCH  --single-branch https://github.com/tensorflow/models.git 
RUN pip install -r models/official/requirements.txt
ENV PYTHONPATH=/source/models

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["echo TensorFlow Model Garden image"]

