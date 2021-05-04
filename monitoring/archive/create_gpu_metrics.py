# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A command line utility that creates custom Cloud Monitoring metrics
for tracking GPU and GPU memory utilization."""

from google.cloud import monitoring_v3

from absl import app
from absl import flags
from absl import logging

GPU_UTILIZATION_METRIC_NAME = 'gce/gpu/utilization'
GPU_UTILIZATION_METRIC_DESC = 'GPU utilization'
GPU_MEMORY_UTILIZATION_METRIC_NAME = 'gce/gpu/memory_utilization'
GPU_MEMORY_UTILIZATION_METRIC_DESC = 'GPU memory utilization'

FLAGS = flags.FLAGS

flags.DEFINE_string('project_id', None, 'GCP Project ID') 
flags.mark_flag_as_required('project_id')

def create_gpu_metrics(project_id):
    "Creates metrics that monitor GPU utilization."

    def _create_metric_descriptor(name, description):
        "Creates a GAUGE/INT64 metric descriptor."

        descriptor = monitoring_v3.types.MetricDescriptor()
        descriptor.type = f'custom.googleapis.com/{name}'
        descriptor.metric_kind =  monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE
        descriptor.value_type =  monitoring_v3.enums.MetricDescriptor.ValueType.INT64
        descriptor.description = description
        descriptor = client.create_metric_descriptor(project_name, descriptor)
        print(descriptor)

    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(project_id)

    _create_metric_descriptor(GPU_UTILIZATION_METRIC_NAME,
                              GPU_UTILIZATION_METRIC_DESC)
    _create_metric_descriptor(GPU_MEMORY_UTILIZATION_METRIC_NAME,
                              GPU_MEMORY_UTILIZATION_METRIC_DESC)
                            

def main(argv):
    del argv
    create_gpu_metrics(FLAGS.project_id)

if __name__ == '__main__':
    app.run(main)