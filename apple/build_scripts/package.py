# -*- coding: utf-8 -*-
import os
import sys  # orez-rm

sys.path.append(os.getcwd())  # orez-rm
import utils  # orez-rm

name = "materialx"

version = utils.package_version()  # orez-sub: PACKAGE_VERSION

build_command = utils.build_command()  # orez-rm

format_version = 2

commit = utils.commit_hash()  # orez-sub: COMMIT_HASH

timestamp = 0  # orez-sub: TIMESTAMP

private_build_requires = utils.build_requires()  # orez-rm

variants = utils.rez_variant_list()  # orez-sub: VARIANT_LIST

def commands():
    env.PATH.append("{root}/bin")
    env.PYTHONPATH.append("{root}/python")



