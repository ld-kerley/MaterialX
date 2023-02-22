import os
import sys
import utils

sys.path.append(os.path.dirname(os.environ["REZ_USED"]))

name = os.environ["REZ_BUILD_PROJECT_NAME"]
version = os.environ["REZ_BUILD_PROJECT_VERSION"]
root = os.environ["REZ_BUILD_INSTALL_PATH"]
keys = [k for k in root.split(version)[-1].split(os.path.sep) if k]

variant_name, data = utils.variant_by_keys(keys)
print("Building {}".format(variant_name))
utils.build(data, root, exact_root=True, xcrun=utils.should_use_xcrun())


destination = os.path.join('/usr/local/apps/', name, version)
utils.fix_rpaths(start=root, destination=destination, index=data['id'])