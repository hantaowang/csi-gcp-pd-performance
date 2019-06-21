import os
import tempfile
import time
import json
from utils import execute, set_env_if_true

tmp_dirs = []


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
	td = tempfile.TemporaryDirectory()
	tmp_dirs.append(td)
	return td


def wait_for_all(resource, state_desired, num_desired, labels=None, kubeconfig=None):
	time_finished = {}

	while True:
		try:
			descriptions = get_descriptions(resource, labels=labels, kubeconfig=kubeconfig)
		except json.decoder.JSONDecodeError:
			time.sleep(0.5)
			continue

		statuses = list(map(lambda x: x['status']['phase'], descriptions['items']))
		names = list(map(lambda x: x['metadata']['name'], descriptions['items']))
		for i in range(len(names)):
			if statuses[i] == state_desired and names[i] not in time_finished:
				time_finished[names[i]] = time.time()
		if statuses.count(state_desired) == num_desired:
			break
		print("Expected {} {} in {} phase, but found {}".format(num_desired, resource, state_desired,
																statuses.count(state_desired)), end='\r')
	print("")
	return time_finished


def get_descriptions(resource, labels=None, kubeconfig=None):
	cmd = ['kubectl', 'get', resource, '-o', 'json']
	if labels is not None and isinstance(labels, dict):
		cmd.append('-l')
		s = ''
		for k, v in labels.items():
			s += '{}={}'.format(k, v)
			s += ','
		if s[-1] == ',':
			s = s[:-1]
		cmd.append(s)
	return json.loads(execute(cmd, env=set_env_if_true('KUBECONFIG', kubeconfig), hide_output=True, hide_cmd=True))
