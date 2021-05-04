import time

from google.cloud import monitoring_v3

from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string('project_id', 'jk-mlops-dev', 'GCP Project ID') 
flags.DEFINE_string('instance_id', 'jk-mlops-dev', 'Instance ID') 
flags.DEFINE_string('zone', 'us-west1-b', 'Zone')
flags.DEFINE_integer('update_freq', 9, 'Update frequency')  


def write_metric():
    project_name = "projects/{}".format(FLAGS.project_id)

    client = monitoring_v3.MetricServiceClient()
    series = monitoring_v3.types.TimeSeries()

    series.metric.type = 'custom.googleapis.com/gce/gpu/utilization'

    series.resource.type = 'gce_instance'
    series.resource.labels['instance_id'] = FLAGS.instance_id
    series.resource.labels['zone'] = FLAGS.zone

    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10 ** 9)
    
    point = series.points.add()
    point.interval.end_time.seconds = seconds
    point.interval.end_time.nanos = nanos
    point.value.int64_value = 20  

    client.create_time_series(name=project_name, time_series=[series])

def main(argv):
    del argv

    for i in range(10):
        write_metric()
        time.sleep(FLAGS.update_freq)
        print('Wrote metric')



if __name__ == '__main__':
    app.run(main)