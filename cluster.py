import json
import os
import uuid
from resources import get_tmp_dir, template, deploy
from utils import execute, set_env_if_true

BASE_CLUSTER_NAME = 'test-cluster'


def cluster_up(name, recreate_if_exists=True, **kwargs):

    num_nodes = kwargs.get('num_nodes', 1)
    machine_type = kwargs.get('machine_type', 'n1-standard-16')
    cluster_version = kwargs.get('cluster_version', 'latest')
    release_channel = kwargs.get('release_channel', None)
    zone = kwargs.get('zone', 'us-central1-a')

    if len(check_cluster_status(name, zone)):
        if recreate_if_exists:
            cluster_down(name, zone)
        else:
            return
    if release_channel is not None:
        execute(['gcloud', 'alpha', 'container', 'clusters', 'create', name, '--num-nodes',
                 num_nodes, '--machine-type', machine_type, '--release-channel',
                 release_channel, '--zone', zone, '--quiet'])
    else:
        execute(['gcloud', 'container', 'clusters', 'create', name, '--num-nodes',
                 num_nodes, '--machine-type', machine_type, '--cluster-version',
                 cluster_version, '--zone', zone, '--quiet'])


def check_cluster_status(name=None, zone=None):
    """
    If name is a string, returns a list with the dict for that cluster, if it exists
    If name is a list of strings, returns a list of dicts
    If name is None, returns a list of dicts for all clusters
    """
    cmd = ['gcloud', 'container', 'clusters', 'list', '--format', 'json']
    if zone is not None:
        cmd.extend(["--zone", zone])
    all_data = json.loads(execute(cmd, hide_output=True))
    if isinstance(name, str):
        for c in all_data:
            if c['name'] == name:
                return [c]
    elif isinstance(name, list):
        to_return = []
        for c in all_data:
            if c['name'] == name:
                to_return.append(c)
        return to_return
    elif name is None:
        return all_data

    return []


def cluster_down(name, zone='us-central1-a', background=False):
    cmd = ['gcloud', 'container', 'clusters', 'delete', name, '--zone', zone, '--quiet']
    if background:
        cmd.append('--async')
    execute(cmd)


def get_cluster_credentials(name, kubeconfig, zone='us-central1-a'):

    execute(['gcloud', 'container', 'clusters', 'get-credentials', name, '--zone', zone],
            env={'KUBECONFIG': kubeconfig})
    print("Wrote kube config to {}".format(kubeconfig))


def install_driver(gce_pd_dir, staging_image, kubeconfig=None):
    execute(['make', "-C", gce_pd_dir, "test-k8s-integration"])

    args = [
        '--run-in-prow=false',
        '--staging-image', staging_image,
        '--service-account-file', os.path.join(gce_pd_dir, "cloud-sa.json"),
        '--deploy-overlay-name', 'dev',
        '--bringup-cluster=false',
        '--teardown-cluster=false',
        '--teardown-driver=false'
    ]

    unused_args = [
        '--test-focus', 'External.Storage',
        '--gce-zone', 'us-central1-a',
    ]

    cmd = [os.path.join(gce_pd_dir, "bin/k8s-integration-test")]
    cmd.extend(args)
    cmd.extend(unused_args)

    execute(cmd, env=set_env_if_true('KUBECONFIG', kubeconfig))


def set_up_cluster(**kwargs):
    cluster_name = BASE_CLUSTER_NAME + "-" + str(uuid.uuid4())[:4]

    kube_tmp_dir = get_tmp_dir()
    kube_config = str(os.path.join(kube_tmp_dir.name, "config"))

    cluster_up(cluster_name, recreate_if_exists=False, **kwargs)
    get_cluster_credentials(cluster_name, kube_config)

    return cluster_name, kube_config


def use_existing_cluster(cluster_name, **kwargs):
    kube_tmp_dir = get_tmp_dir()
    kube_config = str(os.path.join(kube_tmp_dir.name, "config"))
    get_cluster_credentials(cluster_name, kube_config, **kwargs)

    return kube_config
