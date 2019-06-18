import os
import tempfile
import time
from utils import execute, set_env_if_true


def write_to_tempfile(s, tempdir=None):
	if isinstance(tempdir, tempfile.TemporaryDirectory):
		tempdir = tempdir.name

	fd, path = tempfile.mkstemp(dir=tempdir, text=True, suffix='.yaml')
	os.write(fd, bytes(s, 'UTF-8'))
	os.close(fd)

	return path


def template(path, replacements, tempdir=None):
	"""
	:param path: the path of the manifest to template
	:param replacements: a dictionary of values to replace
	:param tempdir: optional arg to specify directory to tempfile
	:return: the path to the temporary file
	"""
	with open(path, "r") as f:
		s = f.read()
		for k, v in replacements.items():
			s = s.replace(k, v)

	return write_to_tempfile(s, tempdir)


def deploy(path, kubeconfig=None):
	"""
	calls kubectl apply on a path
	"""
	execute(['kubectl', 'apply', '-f', path], env=set_env_if_true('KUBECONFIG', kubeconfig))


def delete(path=None, resource_dict=None, kubeconfig=None):
	"""
	calls kubectl delete on a resource. One of the following must be set
	1) path, the path to a manifest file
	2) resource_dict, a dict defining name, namespace, and resource
	"""
	assert any([path, resource_dict]), "One argument must be not none"

	args = []

	if path is not None:
		args.extend(["-f", path])
	else:
		args.extend([resource_dict["resource"], resource_dict["name"], "-n", resource_dict["namespace"]])

	cmd = ["kubectl", "delete"] + args
	execute(cmd, env=set_env_if_true('KUBECONFIG', kubeconfig))


def get_tmp_dir():
	return tempfile.TemporaryDirectory()


def wait_for_all(resource, desired, kubeconfig=None):
	while True:
		statuses = get_statuses(resource, kubeconfig=kubeconfig)
		if statuses.count(desired) == len(statuses):
			break
		print("Expected {} of {}, but found {}".format(len(statuses), resource, statuses.count(desired)))
		time.sleep(1)


def get_statuses(resource, kubeconfig=None):
	cmd = ['kubectl', 'get', resource, '-o', 'jsonpath={.items[*].status.phase}']
	return execute(cmd, env=set_env_if_true('KUBECONFIG', kubeconfig)).split()
