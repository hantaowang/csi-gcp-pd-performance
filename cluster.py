import json
import subprocess

def cluster_up(name, delete_if_exists = True, **kwargs):

  num_nodes = kwargs.get('num_nodes', 1)
  machine_type = kwargs.get('machine_type', 'n1-standard-16')
  cluster_version = kwargs.get('cluster_version', 'latest')
  zone = kwargs.get('zone', 'us-central1-a')

  subprocess.check_output(['gcloud', 'container', 'clusters', 'create', name, '--num-nodes',
                           num_nodes, '--machine-type', machine_type, '--cluster-version',
                           cluster_version, '--zone', zone, '--quiet'])


def check_cluster_status(name, zone='us-central1-a'):

