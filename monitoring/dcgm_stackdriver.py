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

"""A command line utility that monitors attached GPUs and 
reports the stats to Cloud Monitoring"""

import requests
import time
import datetime
import dcgm_fields

from absl import app
from absl import flags
from absl import logging

from google.api_core import exceptions
from google.cloud import monitoring_v3

from DcgmReader import DcgmReader

FLAGS = flags.FLAGS

FIELD_GROUP_NAME = 'dcgm_stackdriver'
GLOBAL_RESOURCE_TYPE = 'global'
GCE_RESOUCE_TYPE = 'gce_instance'

# DCGM fields to SD metrics mapping
DCGM_FIELDS = {
    # Equivalents of the basic metrics in nvidia-smi
    dcgm_fields.DCGM_FI_DEV_GPU_UTIL: # 203
        {
            'name': 'custom.googleapis.com/gce/gpu-test/utilization',
            'desc': 'GPU utilization',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64,
            'sd_units': '%',
            #'value_converter': (lambda x: x) 
        },
    dcgm_fields.DCGM_FI_DEV_FB_USED: # 252
        {
            'name': 'custom.googleapis.com/gce/gpu-test/mem_used',
            'desc': 'GPU memory used',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            'sd_units': 'MBy',
            #'value_converter': (lambda x: x)
        },
    dcgm_fields.DCGM_FI_DEV_POWER_USAGE: #155
        {
            'name': 'custom.googleapis.com/gce/gpu-test/power_usage',
            'desc': 'Power usage',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'sd_units': 'watt',
            #'value_converter': (lambda x: int(x))
        },
    # Profiling metrics recommended by NVidia
    dcgm_fields.DCGM_FI_PROF_GR_ENGINE_ACTIVE: # 1001
        {
            'name': 'custom.googleapis.com/gce/gpu-test/gr_engine_active',
            'desc': 'Ratio of time the graphics engine is active',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'sd_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))
        },
    dcgm_fields.DCGM_FI_PROF_SM_ACTIVE: # 1002 
        {
            'name': 'custom.googleapis.com/gce/gpu-test/sm_active',
            'desc': 'Ratio of cycles an SM has at least 1 warp assigned',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE,  
            'sd_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))
        },
    dcgm_fields.DCGM_FI_PROF_SM_OCCUPANCY: # 1003
        {
            'name': 'custom.googleapis.com/gce/gpu-test/sm_occupancy',
            'desc': 'Ratio of number of warps resident on an SM',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'sd_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))            
        },
    dcgm_fields.DCGM_FI_PROF_DRAM_ACTIVE: # 1005
        {
            'name': 'custom.googleapis.com/gce/gpu-test/memory_active',
            'desc': 'Ratio of cycles the device memory inteface is active sending or receiving data',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'sd_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))
        },
    dcgm_fields.DCGM_FI_PROF_PIPE_TENSOR_ACTIVE: # 1004 
        {
            'name': 'custom.googleapis.com/gce/gpu-test/tensor_active',
            'desc': 'Ratio of cycles the tensor cores are active',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'sd_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))
        },
    dcgm_fields.DCGM_FI_PROF_PIPE_FP32_ACTIVE: # 1007
        {
            'name': 'custom.googleapis.com/gce/gpu-test/fp32_active',
            'desc': 'Ratio of cycles the FP32 cores are active',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE, 
            'sd_units': 'ratio',
            #'value_converter': (lambda x: int(100 * x))
        },
    dcgm_fields.DCGM_FI_PROF_PCIE_TX_BYTES: # 1011
        {
            'name': 'custom.googleapis.com/gce/gpu-test/pcie_tx_throughput',
            'desc': 'PCIE transmit througput',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            #'sd_units': 'number',
            #'value_converter': (lambda x: x) 
        },
    dcgm_fields.DCGM_FI_PROF_PCIE_RX_BYTES:
        {
            'name': 'custom.googleapis.com/gce/gpu-test/pcie_rx_throughput',
            'desc': 'PCIE receive througput',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            #'sd_units': 'number',
            #'value_converter': (lambda x: x) 
        },
    dcgm_fields.DCGM_FI_PROF_NVLINK_TX_BYTES:
        {
            'name': 'custom.googleapis.com/gce/gpu-test/nvlink_tx_throughput',
            'desc': 'NVLink transmit througput',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            #'sd_units': 'number',
            #'value_converter': (lambda x: x) 
        },
    dcgm_fields.DCGM_FI_PROF_NVLINK_RX_BYTES:
        {
            'name': 'custom.googleapis.com/gce/gpu-test/nvlink_rx_throughput',
            'desc': 'NVLink receive througput',
            'metric_kind': monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE,
            'value_type': monitoring_v3.enums.MetricDescriptor.ValueType.INT64, 
            #'sd_units': 'number',
            #'value_converter': (lambda x: x) 
        },
    # Future optional metrics. This metrics cannot be retrieved
    # together with the core metrics without a perf/accuracy penalty.
    # They could be used as drill down metrics
    # dcgm_fields.DCGM_FI_DEV_MEM_COPY_UTIL:
    # dcgm_fields.DCGM_FI_PROF_PIPE_FP64_ACTIVE:
    # dcgm_fields.DCGM_FI_PROF_PIPE_FP16_ACTIVE:
}


_GCP_METADATA_URI = 'http://metadata.google.internal/computeMetadata/v1/'
_GCP_METADATA_URI_HEADER = {'Metadata-Flavor': 'Google'}
_GCE_ATTRIBUTES = {
    'project_id': {
        'metadata_key': 'project/project-id'
    },
    'instance_id': {
        'metadata_key': 'instance/id',
    },
    'zone': {
        'metadata_key': 'instance/zone',
        'transformation': 
            lambda x: x.split('/')[-1]
    }
}

def get_gce_resource_labels():
    """Retrieve GCE metadata and sets GCE instance resource labels."""

    resource_labels = {}
    for label, gce_metadata in _GCE_ATTRIBUTES.items():
        response = requests.get(_GCP_METADATA_URI + gce_metadata['metadata_key'], 
                                headers=_GCP_METADATA_URI_HEADER)

        if 'transformation' in _GCE_ATTRIBUTES[label]:
            label_value = _GCE_ATTRIBUTES[label]['transformation'](response.text)
        else:
            label_value = response.text
        resource_labels[label] = label_value.decode('utf-8')

    return resource_labels



class DcgmStackdriver(DcgmReader):
    """
    Custom DCGM reader that pushes DCGM metrics to GCP Cloud Monitoring
    """
 
    def __init__(self, update_frequency, fields_to_watch, project_id, resource_type, resource_labels):
       
        DcgmReader.__init__(self, fieldIds=fields_to_watch.keys(), 
                            fieldGroupName=FIELD_GROUP_NAME, 
                            updateFrequency=update_frequency * 1000 * 1000)
        
        self._fields_to_watch = fields_to_watch
        self._project_id = project_id
        self._resource_type = resource_type
        self._resource_labels = resource_labels

        self._client =  monitoring_v3.MetricServiceClient()
        self._project_name = self._client.project_path(self._project_id)
        self._create_sd_metric_descriptors()
        self._counter = 0
    
    def _create_sd_metric_descriptors(self):
        """
        Creates SD metric descriptors for the watched DCGM fields.
        """
        project_name = self._client.project_path(self._project_id) 
        for key, item in self._fields_to_watch.items():
            descriptor = monitoring_v3.types.MetricDescriptor()
            descriptor.type = item['name']
            descriptor.metric_kind = item['metric_kind'] 
            descriptor.value_type =  item['value_type']
            descriptor.description = item['desc']
            if 'sd_units' in item.keys():
                descriptor.unit = item['sd_units']
            descriptor = self._client.create_metric_descriptor(project_name, descriptor)


    def _add_point(self, series, field_id, field):
        """Adds a point to SD time series."""

        if 'value_converter' in self._fields_to_watch[field_id]:
            field_value = self._fields_to_watch[field_id]['value_converter'](field.value)
        else:
            field_value = field.value 

        seconds = field.ts // 10**6
        nanos = (field.ts % 10**6) * 10**3
        point = series.points.add()
        point.interval.end_time.seconds = seconds
        point.interval.end_time.nanos = nanos 

        sd_value_type = self._fields_to_watch[field_id]['value_type']
        if sd_value_type == monitoring_v3.enums.MetricDescriptor.ValueType.INT64:
            point.value.int64_value = field_value
        elif sd_value_type == monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE:
            point.value.double_value = field_value
        elif sd_value_type == monitoring_v3.enums.MetricDescriptor.ValueType.BOOL:
            point.value.bool = field_value 
        elif sd_value_type == monitoring_v3.enums.MetricDescriptor.ValueType.STRING: 
            point.value.string = field_value
        else:
            raise TypeError('Unsupported metric type: {}'.format(sd_value_type))


    def _construct_sd_series(self, field_id, field_time_series, metric_labels):
        """Constructs SD time series from the DCGM field time_series."""

        series = None
        field = field_time_series[-1]
        if (field_id in self._fields_to_watch.keys()) and (not field.isBlank):

            series = monitoring_v3.types.TimeSeries()
            series.resource.type = self._resource_type
            for label_key, label_value in self._resource_labels.items():
                series.resource.labels[label_key] = label_value

            series.metric.type = self._fields_to_watch[field_id]['name']
            for label_key, label_value in metric_labels.items():
                series.metric.labels[label_key] = label_value
            self._add_point(series, field_id, field)

        return series


    def _create_time_series(self, fvs):
        """
        Calls SD to create time series based on the latest values
        of DCGM watched fields/
        """
        time_series = []
        for gpu in fvs:
            for field_id, field_time_series in fvs[gpu].items():
                metric_labels = {'gpu': str(gpu)}
                series = self._construct_sd_series(field_id, field_time_series, metric_labels)
                if series:
                    time_series.append(series)
        
        if time_series:
            try:
                self._client.create_time_series(
                    name=self._project_name, 
                    time_series=time_series)
                logging.info('Successfully logged time series')
            except exceptions.GoogleAPICallError as err:
                logging.info(err)
            except exceptions.RetryError as err:
                logging.info('Retry attempts to create time series failed')
            except Exception:    
                logging.info('Create_time_series: exception encountered')
            
        
    def CustomDataHandler(self, fvs):
        """
        Writes reported field values to Cloud Monitoring.
        """

        self._counter += 1 
        # Skip the first measurement to avoid duplicates in DCGM
        if self._counter > 1:
            self._create_time_series(fvs)
    
    def LogInfo(self, msg):
        logging.info(msg)  # pylint: disable=no-member

    def LogError(self, msg):
        logging.info(msg)  # pylint: disable=no-member


def main(argv):
    del argv
    
    logging.info("main()")
    logging.info("Project ID:" + FLAGS.project_id)

    logging.info('Entering monitoring loop with update interval: ' + str(FLAGS.update_interval))

    # Only GCE resource type supported at this point
    # In future GKE will be added
    if FLAGS.resource_type == GCE_RESOUCE_TYPE:
        resource_labels = get_gce_resource_labels()
        resource_type = GCE_RESOUCE_TYPE
    else:
        raise ValueError('Unsupported resource type: {}'.format(FLAGS.resource_type))

    with DcgmStackdriver(fields_to_watch=DCGM_FIELDS, 
                         update_frequency=FLAGS.update_interval,
                         project_id=FLAGS.project_id,
                         resource_type=resource_type,
                         resource_labels=resource_labels) as dcgm_reader:
        
        nexttime = time.time()
        try:
            while True:
            #while False:
                dcgm_reader.Process()
                nexttime += FLAGS.update_interval
                sleep_time = nexttime - time.time() 
                if sleep_time > 0:
                    time.sleep(sleep_time)
        except KeyboardInterrupt:
            logging.info("Caught CTRL-C. Exiting ...")

# Command line parameters
flags.DEFINE_integer('update_interval', 10, 'Metrics update frequency - seconds', 
                     lower_bound=10)
flags.DEFINE_enum('resource_type', 'gce_instance', ['gce_instance'], 'Stackdriver resource type')
flags.DEFINE_string('project_id', None, 'GCP Project ID')
flags.mark_flag_as_required('project_id')

if __name__ == '__main__':
    # Run app
    app.run(main)
