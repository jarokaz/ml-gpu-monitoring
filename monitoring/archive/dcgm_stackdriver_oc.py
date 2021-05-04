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

import time
import dcgm_fields

from absl import app
from absl import flags
from absl import logging

from DcgmReader import DcgmReader

from opencensus.ext.stackdriver import stats_exporter
from opencensus.stats import aggregation
from opencensus.stats import measure
from opencensus.stats import stats
from opencensus.stats import view
from opencensus import tags



FLAGS = flags.FLAGS



# Mapping DCGM fields to OC metrics
FIELDS_TO_OC = {
    dcgm_fields.DCGM_FI_DEV_POWER_USAGE:
        {
            'name': 'power_usage',
            'desc': 'power usage',
            'units': 'Watts',
            'buckets': [], 
        },
    dcgm_fields.DCGM_FI_DEV_GPU_UTIL:
        {
            'name': 'gpu_utilization',
            'desc': 'GPU utilization',
            'units': '%',
            'buckets': [11, 21, 31, 41, 51, 61, 71, 81, 91, 101],
        },
    dcgm_fields.DCGM_FI_DEV_MEM_COPY_UTIL:
        {
            'name': 'mem_cpu_utilization',
            'desc': 'memory copy utilization',
            'units': '%',
            'buckets': [11, 21, 31, 41, 51, 61, 71, 81, 91, 101],
        },
    dcgm_fields.DCGM_FI_PROF_DRAM_ACTIVE:
        {
            'name': 'memory_active',
            'desc': 'ratio of cycles the device memory inteface is active sending or receiving data',
            'units': 'ratio',
            'buckets': [11, 21, 31, 41, 51, 61, 71, 81, 91, 101],
        },
    dcgm_fields.DCGM_FI_DEV_FB_TOTAL:
        {
            'name': 'fb_total',
            'desc': 'Total framebuffer memory',
            'units': 'MBs',
        },
    dcgm_fields.DCGM_FI_DEV_FB_FREE:
        {
            'name': 'fb_free',
            'desc': 'Free framebuffer memory',
            'units': 'MBs',
        },
    dcgm_fields.DCGM_FI_DEV_FB_USED:
        {
            'name': 'fb_used',
            'desc': 'Used framebuffer memory',
            'units': 'MBs',
        },
    dcgm_fields.DCGM_FI_PROF_GR_ENGINE_ACTIVE:
        {
            'name': 'gr_engine_active',
            'desc': 'ratio of time the graphics engine is active',
            'units': 'ratio',
            'buckets': [11, 21, 31, 41, 51, 61, 71, 81, 91, 101], 
        },
    dcgm_fields.DCGM_FI_PROF_SM_ACTIVE: # 1
        {
            'name': 'sm_active',
            'desc': 'ratio of cycles an SM has at least 1 warp assigned',
            'units': 'ratio',
            'buckets': [11, 21, 31, 41, 51, 61, 71, 81, 91, 101], 
        },
    dcgm_fields.DCGM_FI_PROF_SM_OCCUPANCY: # 1
        {
            'name': 'sm_occupancy',
            'desc': 'ratio of number of warps resident on an SM',
            'units': 'ratio',
            'buckets': [11, 21, 31, 41, 51, 61, 71, 81, 91, 101], 
        },
    dcgm_fields.DCGM_FI_PROF_PIPE_TENSOR_ACTIVE: # 2
        {
            'name': 'tensor_active',
            'desc': 'ratio of cycles the tensor cores are active',
            'units': 'ratio',
            'buckets': [11, 21, 31, 41, 51, 61, 71, 81, 91, 101], 
        },
    dcgm_fields.DCGM_FI_PROF_PIPE_FP32_ACTIVE:
        {
            'name': 'fp32_active',
            'desc': 'ratio of cycles the FP32 cores are active',
            'units': 'ratio',
            'buckets': [11, 21, 31, 41, 51, 61, 71, 81, 91, 101], 
        },
    dcgm_fields.DCGM_FI_PROF_PCIE_TX_BYTES:
        {
            'name': 'pcie_tx_throughput',
            'desc': 'PCIE transmit througput',
            'units': 'bytes per second',
            'buckets': [], 
        },
    dcgm_fields.DCGM_FI_PROF_PCIE_RX_BYTES:
        {
            'name': 'pcie_rx_throughput',
            'desc': 'PCIE receive througput',
            'units': 'bytes per second',
            'buckets': [], 
        },
    dcgm_fields.DCGM_FI_PROF_NVLINK_TX_BYTES:
        {
            'name': 'nvlink_tx_throughput',
            'desc': 'NVLink transmit througput',
            'units': 'bytes per second',
            'buckets': [], 
        },
    dcgm_fields.DCGM_FI_PROF_NVLINK_RX_BYTES:
        {
            'name': 'nvlink_rx_throughput',
            'desc': 'NVLink receive througput',
            'units': 'bytes per second',
            'buckets': [], 
        },
}

def create_stackdriver_exporter():
    """
    Creates OpenCensus metrics and views and registers
    them with Cloud Monitoring exporter
    """
    # Define OpenCensus measures
    gpu_utilization_ms = measure.MeasureInt(
        'gpu_utilization',
        'GPU utilization',
        '%'
    )
    gpu_memory_utilization_ms = measure.MeasureInt(
        'gpu_memory_utilization',
        'GPU memory utilization',
        '%'
    )
    gpu_power_utilization_ms = measure.MeasureInt(
        'gpu_power_utilization',
        'GPU Power utilization',
        '%'
    )
    
    # Define OpenCensus views
    key_device = tags.tag_key.TagKey("device")
    
    gpu_utilization_view = view.View(
        'gce/gpu/utilization_distribution',
        'The distribution of gpu utilization',
        [key_device],
        gpu_utilization_ms,
        aggregation.DistributionAggregation(
            [11, 21, 31, 41, 51, 61, 71, 81, 91, 101]
        )
    )
    gpu_memory_utilization_view = view.View(
        'gce/gpu/memory_utilization_distribution',
        'The distribution of gpu memory utilization',
        [key_device],
        gpu_memory_utilization_ms,
        aggregation.DistributionAggregation(
            [11, 21, 31, 41, 51, 61, 71, 81, 91, 101]
        )
    )
    gpu_power_utilization_view  = view.View(
        'gce/gpu/power_utilization_distribution',
        'The distribution of power utilization',
        [key_device],
        gpu_power_utilization_ms,
        aggregation.DistributionAggregation(
            [11, 21, 31, 41, 51, 61, 71, 81, 91, 101]
        )
    )
    
    stats.stats.view_manager.register_view(gpu_utilization_view)
    stats.stats.view_manager.register_view(gpu_memory_utilization_view)
    stats.stats.view_manager.register_view(gpu_power_utilization_view)
    
    

    
    # Create Cloud Monitoring stats exporter
    exporter_options = stats_exporter.Options(project_id=FLAGS.project_id,
                                              default_monitoring_labels={})
    exporter = stats_exporter.new_stats_exporter(options=exporter_options,
                                                 interval=FLAGS.reporting_interval)
    
    # Register exporter to the view manager.
    stats.stats.view_manager.register_exporter(exporter)

FIELD_GROUP_NAME = 'dcgm_stackdriver'

class DcgmStackdriver(DcgmReader):
    """
    Custom DCGM reader that pushes DCGM metrics to GCP Cloud Monitoring
    """
    def __init__(self):
        # Set DCGM update frequency to half of the sampling interval
        # to avoid reporting the same reading multiple times
        update_frequency = FLAGS.update_interval * 1000
        logging.info('Initializing DCGM with update frequency={} ms'.format(FLAGS.update_interval))
        DcgmReader.__init__(self, fieldIds=list(FIELDS_TO_OC.keys()), 
                            fieldGroupName=FIELD_GROUP_NAME, 
                            updateFrequency=update_frequency)


    def _define_oc_metrics():
        """
        Creates and registers Open Census metrics.
        """



    def CustomDataHandler(self, fvs):
        """
        Writes reported field values to Cloud Monitoring.
        """
        #for gpuId in fvs.keys():
        #    gpuFv = fvs[gpuId]
        #    print(gpuFv)
        #    print('*****************')
        print("**** Data handler called")
        gpuFv = fvs[0]
        print(fvs)
        for field, value in fvs[0].items():
            print(field, value[-1].value)

    
    def LogInfo(self, msg):
        logging.info(msg)  # pylint: disable=no-member

    def LogError(self, msg):
        logging.info(msg)  # pylint: disable=no-member





def main(argv):
    del argv
    
    logging.info("main()")
    logging.info("Project ID:" + FLAGS.project_id)

    logging.info('Entering monitoring loop with update interval: ', FLAGS.update_interval)
    
    #tmap = tags.tag_map.TagMap()
    #tmap.insert(key_device, tags.tag_value.TagValue("0"))
    
    with DcgmStackdriver() as dcgm_reader:
        try:
            while True:
                #metrics = get_gpu_metrics()
                #for device_index in range(len(metrics)):
                #    mmap = stats.stats.stats_recorder.new_measurement_map()
                #    
                #    mmap.measure_int_put(gpu_utilization_ms, metrics[device_index]['utilization']['gpu_util'])
                #    mmap.measure_int_put(gpu_memory_utilization_ms, metrics[device_index]['utilization']['memory_util'])
                #    power_percentage = metrics[device_index]['power_readings']['power_draw'] / metrics[device_index]['power_readings']['power_limit']
                #    #logging.info(round(power_percentage,2))
                #    mmap.measure_int_put(gpu_power_utilization_ms, round(power_percentage,2))
                #    
                #    tmap.update(key_device, tags.tag_value.TagValue(str(device_index)))
                #    mmap.record(tmap)
                    #logging.info(mmap)
                    #logging.info(tmap)
                
                time.sleep(FLAGS.update_interval/1000)
                dcgm_reader.Process()
        except KeyboardInterrupt:
            print("Caught CTRL-C. Exiting ...")

flags.DEFINE_integer('update_interval', 3000, 'DCGM update frequency - miliseconds', 
                     lower_bound=1)
flags.DEFINE_string('project_id', None, 'GCP Project ID')
flags.mark_flag_as_required('project_id')

if __name__ == '__main__':
    app.run(main)
