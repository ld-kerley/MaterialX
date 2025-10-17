#!/usr/bin/env bash

# Copyright Contributors to the OpenImageIO project.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/AcademySoftwareFoundation/OpenImageIO

# This script is run when CI system first starts up.
# Since it sets many env variables needed by the caller, it should be run
# with 'source', not in a separate shell.

# Environment variables we always need
export PATH=/usr/local/bin/_ccache:/usr/lib/ccache:$PATH
export USE_CCACHE=${USE_CCACHE:=1}
export CCACHE_CPP2=
export CCACHE_DIR=$HOME/.ccache
export CCACHE_COMPRESSION=yes
if [[ "$(which ccache)" != "" ]] ; then
    # Try to coax dependency building into also using ccache
    export CMAKE_CXX_COMPILER_LAUNCHER="ccache"
    export CMAKE_C_COMPILER_LAUNCHER="ccache"
    ccache -z
fi
mkdir -p $CCACHE_DIR



echo "HOME = $HOME"
echo "PWD = $PWD"
echo "LOCAL_DEPS_DIR = $LOCAL_DEPS_DIR"
echo "uname -a: " `uname -a`
echo "uname -m: " `uname -m`
echo "uname -s: " `uname -s`
echo "uname -n: " `uname -n`
pwd
ls
env | sort

if [[ `uname -s` == "Linux" ]] ; then
    echo "nprocs: " `nproc`
    head -40 /proc/cpuinfo
elif [[ "${RUNNER_OS}" == "macOS" ]] ; then
    echo "nprocs: " `sysctl -n hw.ncpu`
    sysctl machdep.cpu.features
fi

# Save the env for use by other stages
scripts/save-env.bash
