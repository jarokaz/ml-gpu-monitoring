from google.cloud import monitoring_v3

from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string('project_id', 'jk-mlops-dev', 'GCP Project ID') 

def main(argv):
    del argv

    client = monitoring_v3.MetricServiceClient()
    project_name = "projects/{}".format(FLAGS.project_id)
    for descriptor in client.list_metric_descriptors(name=project_name):
        print(descriptor.name)

if __name__ == '__main__':
    app.run(main)