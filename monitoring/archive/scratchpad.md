docker run -it --rm --gpus device=1 \
--env OUTPUT_DIR=gs://jk-bert-lab-bucket \
--env TASK=MNLI \
--env PARAMS=\
task.train_data.input_path=gs://jk-bert-lab-bucket/data/MNLI/MNLI_train.tf_record,\
task.validation_data.input_path=gs://jk-bert-lab-bucket/data/MNLI/MNLI_eval.tf_record,\
task.init_checkpoint=gs://cloud-tpu-checkpoints/bert/keras_bert/uncased_L-24_H-1024_A-16,\
task.train_data.global_batch_size=8,\
task.validation_data.global_batch_size=8,\
runtime.distribution_strategy=mirrored,\
runtime.num_gpus=2 \
gcr.io/jk-mlops-dev/model-garden-tf24 \
'python3 train.py \
 --start_profiler \
 --experiment=bert/sentence_prediction \
 --mode=train_and_eval \
 --model_dir=$OUTPUT_DIR/models/$TASK \
 --config_file=models/official/nlp/configs/experiments/glue_mnli_matched.yaml \
 --params_override=$PARAMS' 