import time
import os
import uuid
from resources import *
from cluster import *

NUM_PVS_PER_POD = 2
NUM_POD = 64
PVC_SIZE = '10Gi'
BASE_CLUSTER_NAME = 'test-cluster-alpha'

def set_up_cluster():
	cluster_name = BASE_CLUSTER_NAME + "-" + str(uuid.uuid4())[:4]

	kube_tmp_dir = get_tmp_dir()
	kube_config = os.path.join(kube_tmp_dir.name, "config")

	cluster_up(cluster_name, recreate_if_exists=False, release_channel='rapid')
	get_cluster_credentials(cluster_name, kube_config)

	install_driver(kubeconfig=kube_config)

	return cluster_name, kube_config

def basic_test():

	cluster_name, kube_config = set_up_cluster()

	sc = template("manifests/storage-class.yaml", {})

	pods_tmp_dir = get_tmp_dir()
	pvc_tmp_dir = get_tmp_dir()

	for i in range(NUM_POD * NUM_PVS_PER_POD):
		template("manifests/pvc-template.yaml", {
			'VAR_PVC_NAME': 'pvc' + str(i),
			'VAR_PVC_SIZE': PVC_SIZE,
			'VAR_ACCESS_MODE': 'ReadWriteOnce',
		}, tempdir=pvc_tmp_dir)

	for i in range(NUM_POD):
		template("manifests/pod-template.yaml", {
			'VAR_PVC_NAME1': 'pvc' + str(i),
			'VAR_PVC_NAME2': 'pvc' + str(i + NUM_POD),
			'VAR_POD_NAME': 'pod' + str(i),
		}, tempdir=pods_tmp_dir)

	deploy(path=sc, kubeconfig=kube_config)
	deploy(path=pvc_tmp_dir.name, kubeconfig=kube_config)

	wait_for_all("pvc", "Bound", kubeconfig=kube_config)

	start = time.time()
	deploy(path=pods_tmp_dir.name, kubeconfig=kube_config)
	wait_for_all("pods", "Running", kubeconfig=kube_config)
	end = time.time()

	print("Execution took {} seconds", end - start)
	cluster_down(cluster_name)
	return end - start


if __name__ == '__main__':
	basic_test()
