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

import dcgm_fields

from google.cloud import monitoring_v3

from absl import app
from absl import flags
from absl import logging


FLAGS = flags.FLAGS

flags.DEFINE_string('project_id', None, 'GCP Project ID') 
flags.mark_flag_as_required('project_id')

DCGM_FIELDS = {
    # Equivalents of the basic metrics in nvidia-smi
    dcgm_fields.DCGM_FI_DEV_GPU_UTIL: # 203
        {
            'name': 'custom.googleapis.com/gce/gpu-test/utilization',
            'desc': 'GPU utilization',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64,
            'dcgm_units': '%',
            #'value_converter': (lambda x: x) 
        },
    dcgm_fields.DCGM_FI_DEV_FB_USED: # 252
        {
            'name': 'custom.googleapis.com/gce/gpu-test/mem_used',
            'desc': 'GPU memory used',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            'dcgm_units': 'MBs',
            #'value_converter': (lambda x: x)
        },
    dcgm_fields.DCGM_FI_DEV_POWER_USAGE: #155
        {
            'name': 'custom.googleapis.com/gce/gpu-test/power_usage',
            'desc': 'Power usage',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            'dcgm_units': 'Watts',
            #'value_converter': (lambda x: int(x))
        },
    # Profiling metrics recommended by NVidia
    dcgm_fields.DCGM_FI_PROF_GR_ENGINE_ACTIVE: # 1001
        {
            'name': 'custom.googleapis.com/gce/gpu-test/gr_engine_active',
            'desc': 'Ratio of time the graphics engine is active',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            #'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'dcgm_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))
        },
    dcgm_fields.DCGM_FI_PROF_SM_ACTIVE: # 1002 
        {
            'name': 'custom.googleapis.com/gce/gpu-test/sm_active',
            'desc': 'Ratio of cycles an SM has at least 1 warp assigned',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
 #           'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE,  
            'dcgm_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))
        },
    dcgm_fields.DCGM_FI_PROF_SM_OCCUPANCY: # 1003
        {
            'name': 'custom.googleapis.com/gce/gpu-test/sm_occupancy',
            'desc': 'Ratio of number of warps resident on an SM',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
#            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'dcgm_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))            
        },
    dcgm_fields.DCGM_FI_PROF_DRAM_ACTIVE: # 1005
        {
            'name': 'custom.googleapis.com/gce/gpu-test/memory_active',
            'desc': 'Ratio of cycles the device memory inteface is active sending or receiving data',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
#            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'dcgm_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))
        },
    dcgm_fields.DCGM_FI_PROF_PIPE_TENSOR_ACTIVE: # 1004 
        {
            'name': 'custom.googleapis.com/gce/gpu-test/tensor_active',
            'desc': 'Ratio of cycles the tensor cores are active',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
#            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64,  
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'dcgm_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))
        },
    dcgm_fields.DCGM_FI_PROF_PIPE_FP32_ACTIVE: # 1007
        {
            'name': 'custom.googleapis.com/gce/gpu-test/fp32_active',
            'desc': 'Ratio of cycles the FP32 cores are active',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
#            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'dcgm_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))
        },
    dcgm_fields.DCGM_FI_PROF_PCIE_TX_BYTES: # 1011
        {
            'name': 'custom.googleapis.com/gce/gpu-test/pcie_tx_throughput',
            'desc': 'PCIE transmit througput',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            'dcgm_units': 'Bytes per second',
            #'value_converter': (lambda x: x) 
        },
    dcgm_fields.DCGM_FI_PROF_PCIE_RX_BYTES:
        {
            'name': 'custom.googleapis.com/gce/gpu-test/pcie_rx_throughput',
            'desc': 'PCIE receive througput',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            'dcgm_units': 'Bytes per second',
            #'value_converter': (lambda x: x) 
        },
    dcgm_fields.DCGM_FI_PROF_NVLINK_TX_BYTES:
        {
            'name': 'custom.googleapis.com/gce/gpu-test/nvlink_tx_throughput',
            'desc': 'NVLink transmit througput',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            'dcgm_units': 'Bytes per second',
            #'value_converter': (lambda x: x) 
        },
    dcgm_fields.DCGM_FI_PROF_NVLINK_RX_BYTES:
        {
            'name': 'custom.googleapis.com/gce/gpu-test/nvlink_rx_throughput',
            'desc': 'NVLink receive througput',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            'dcgm_units': 'Bytes per second',
            #'value_converter': (lambda x: x) 
        },
}

def main(argv):
    del argv
    
    client = monitoring_v3.MetricServiceClient()

    parent = 'projects/{}/metricDescriptors/custom.googleapis.com'.format(FLAGS.project_id)
    
    for field, value in DCGM_FIELDS.items():
        name = 'projects/{}/metricDescriptors/{}'.format(FLAGS.project_id, value['name'])
        client.delete_metric_descriptor(name=name)
        print('Deleted: ', name)

if __name__ == '__main__':
    app.run(main)