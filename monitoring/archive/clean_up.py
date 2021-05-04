from google.cloud import monitoring_v3

from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_list('descriptors', [], 'List of descriptors to delete')
flags.DEFINE_string('project_id', 'jk-mlops-dev', 'GCP Project ID') 

def main(argv):
    del argv

    client = monitoring_v3.MetricServiceClient()
    for name in FLAGS.descriptors:
        print(f'Deleting metric: {name}')
        descriptor_name = f'projects/{FLAGS.project_id}/metricDescriptors/custom.googleapis.com/{name}'
        client.delete_metric_descriptor(name=descriptor_name)
    

if __name__ == '__main__':
    app.run(main)