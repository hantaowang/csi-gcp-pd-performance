import time
from resources import template, get_tmp_dir, deploy, wait_for_all, delete
from cluster import set_up_cluster, use_existing_cluster, cluster_down, install_driver
from utils import record_results, SingleTest

NUM_PVS_PER_POD = 1
NUM_POD = 95


class BasicTest(SingleTest):

	common_name = 'basic'

	def setup(self):
		_setup_single_cluster(self)

	def cleanup(self):
		_clean_up(self)

	def _run(self):
		kube_config = self.kwargs['kube_config']
		pods_tmp_dir = get_tmp_dir()
		pvc_tmp_dir = get_tmp_dir()

		for i in range(NUM_POD * NUM_PVS_PER_POD):
			template("manifests/pvc-template.yaml", {
				'VAR_PVC_NAME': 'pvc' + str(i),
				'VAR_PVC_SIZE': '10Gi',
				'VAR_ACCESS_MODE': 'ReadWriteOnce',
			}, tempdir=pvc_tmp_dir)

		for i in range(NUM_POD):
			template("manifests/pod-template.yaml", {
				'VAR_PVC_NAME1': 'pvc' + str(i),
				'VAR_PVC_NAME2': 'pvc' + str(i + NUM_POD),
				'VAR_POD_NAME': 'pod' + str(i),
			}, tempdir=pods_tmp_dir)

		deploy(path=pvc_tmp_dir.name, kubeconfig=kube_config)
		wait_for_all("pvc", "Bound", NUM_POD * NUM_PVS_PER_POD, kubeconfig=kube_config)

		print("config: {}".format(kube_config))
		input("Start")
		start = time.time()
		deploy(path=pods_tmp_dir.name, kubeconfig=kube_config)

		self.kwargs['time_finished'] = wait_for_all("pods", "Running", NUM_POD, labels={
			'purpose': 'experiment',
		}, kubeconfig=kube_config)
		end = time.time()
		self.kwargs['start'] = start
		print("Execution took {} seconds".format(end - start))

		input("Delete")
		delete(path=pods_tmp_dir.name, kubeconfig=kube_config)
		delete(path=pvc_tmp_dir.name, kubeconfig=kube_config)


class OneLargeDiskTest(SingleTest):

	common_name = 'one-large-disk'

	def setup(self):
		_setup_single_cluster(self)

	def cleanup(self):
		_clean_up(self)

	def _run(self):
		kube_config = self.kwargs['kube_config']
		pods_tmp_dir = get_tmp_dir()
		pvc_tmp_dir = get_tmp_dir()

		for i in range(NUM_POD * NUM_PVS_PER_POD):
			if i == NUM_POD * NUM_PVS_PER_POD - 1:
				pvc_size = '1000Gi'
			else:
				pvc_size = '1Gi'
			template("manifests/pvc-template.yaml", {
				'VAR_PVC_NAME': 'pvc' + str(i),
				'VAR_PVC_SIZE': pvc_size,
				'VAR_ACCESS_MODE': 'ReadWriteOnce',
			}, tempdir=pvc_tmp_dir)

		for i in range(NUM_POD):
			template("manifests/pod-template.yaml", {
				'VAR_PVC_NAME1': 'pvc' + str(i),
				'VAR_PVC_NAME2': 'pvc' + str(i + NUM_POD),
				'VAR_POD_NAME': 'pod' + str(i),
			}, tempdir=pods_tmp_dir)

		deploy(path=pvc_tmp_dir.name, kubeconfig=kube_config)
		wait_for_all("pvc", "Bound", NUM_POD * NUM_PVS_PER_POD, kubeconfig=kube_config)

		start = time.time()
		deploy(path=pods_tmp_dir.name, kubeconfig=kube_config)
		self.kwargs['time_finished'] = wait_for_all("pods", "Running", NUM_POD, labels={
			'purpose': 'experiment',
		}, kubeconfig=kube_config)
		end = time.time()
		print("Execution took {} seconds".format(end - start))
		self.kwargs['start'] = start

		delete(path=pods_tmp_dir.name, kubeconfig=kube_config)
		delete(path=pvc_tmp_dir.name, kubeconfig=kube_config)


def _setup_single_cluster(self):
	if 'existing_cluster' in self.kwargs and self.kwargs['existing_cluster']:
		self.kwargs['cluster_name'] = self.kwargs['existing_cluster']
		if 'zone' in self.kwargs and self.kwargs['zone']:
			self.kwargs['kube_config'] = use_existing_cluster(self.kwargs['existing_cluster'], zone=self.kwargs['zone'])
		else:
			self.kwargs['kube_config'] = use_existing_cluster(self.kwargs['existing_cluster'])
	else:
		self.kwargs['cluster_name'], self.kwargs['kube_config'] = set_up_cluster(**self.kwargs)

	install_driver(self.gce_pd_dir, self.staging_image, kubeconfig=self.kwargs['kube_config'])
	sc = template("manifests/storage-class.yaml", {})
	deploy(path=sc, kubeconfig=self.kwargs['kube_config'])


def _clean_up(self):
	name = self.__class__.__name__
	if 'test_name' in self.kwargs:
		name += '-' + self.kwargs['test_name']
	record_results(self.kwargs['time_finished'], self.kwargs['start'], name)
	if 'zone' in self.kwargs and self.kwargs['zone']:
		cluster_down(self.kwargs['cluster_name'], zone=self.kwargs['zone'], background=True)
	else:
		cluster_down(self.kwargs['cluster_name'], background=True)
