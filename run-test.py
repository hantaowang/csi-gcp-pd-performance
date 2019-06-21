import argparse
from single_node_performance import BasicTest, OneLargeDiskTest

DEFAULT_GCE_PD_DIR = '/usr/local/google/home/hww/go/src/sigs.k8s.io/gcp-compute-persistent-disk-csi-driver'
DEFAULT_GCE_PD_CSI_STAGING_IMAGE = 'gcr.io/google.com/hww-devel/gcp-pd-csi-driver-test'

tests_available = [BasicTest, OneLargeDiskTest]

parser = argparse.ArgumentParser(description='Start a test to run')
parser.add_argument('test', help='the test to run')
parser.add_argument('--gce-pd-dir', dest='gcepddir', help='path to the GCE PD directory', default=DEFAULT_GCE_PD_DIR)
parser.add_argument('--gce-pd-csi-image', dest='gcepdcsiimage', help='csi image to stage to', default=DEFAULT_GCE_PD_CSI_STAGING_IMAGE)
parser.add_argument('--use-existing-cluster', dest='existingcluster', help='assume an already existing cluster', default=None)
parser.add_argument('--name', dest='name', help='name for output', default=None)
parser.add_argument('--zone', help='gce zone to work in', default=None)

if __name__ == '__main__':
    args = parser.parse_args()

    for c in tests_available:
        if c.common_name == args.test:
            kwargs = {}
            if args.zone:
                kwargs['zone'] = args.zone
            if args.existingcluster:
                kwargs['existing_cluster'] = args.existingcluster
            if args.name:
                kwargs['test_name'] = args.name
            c(args.gcepddir, args.gcepdcsiimage, kwargs).run()
