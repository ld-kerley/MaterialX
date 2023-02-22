#!/usr/bin/env python


from __future__ import print_function

import collections
import os
import re
import shutil
import subprocess
import json
import argparse
import pprint
import sys
import multiprocessing
import tempfile
import time
import traceback
import zipfile

try:
    import six
except:
    pass

root = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(root, "config.json")
with open(config_path) as fp:
    config = json.load(fp)

repo = os.path.dirname(os.path.dirname(root))


def caffeinate(func):
    def wrapper(*args, **kwargs):
        caffeinate = subprocess.Popen(["caffeinate"])
        try:
            return func(*args, **kwargs)
        finally:
            caffeinate.kill()

    return wrapper


def branch_name():
    branch = (
        subprocess.check_output(["git", "branch", "--show-current"], cwd=repo)
        .decode("utf-8")
        .strip()
    )
    return branch


def build_command():
    return f"{sys.executable} {os.getcwd()}/build.py"


def package_name(branch=None):
    branch = branch or branch_name()
    prefix = branch.split("-")[0]

    name = "usd_{}".format(config["branch_keys"].get(prefix, config["branch_fallback"]))
    return name


def package_version(branch=None):
    from rez.packages_ import iter_packages

    branch = branch or branch_name()
    name = "materialx"
    suffix = name.split("_")[-1]

    if branch.startswith(suffix):
        branch = branch[len(suffix) :]

    if branch.startswith("-"):
        branch = branch[1:]

    rez_build = False
    no_local = False
    no_increment = False
    for arg in sys.argv:
        if __file__ in sys.argv:
            rez_build = True
            continue

        if "rez-build" in arg:
            rez_build = True
            continue

        if "--no-local" in arg:
            no_local = True
            continue

        if "--no-increment" in arg or "--increment=0" in arg:
            no_increment = True
            continue

    local = rez_build and not no_local
    if local:
        branch = "local"

    version = "{}-{}-a".format(branch, materialx_version_string())
    suffix = -1

    for package in iter_packages(name):
        ver = str(package.version)
        if not ver.startswith(version):
            continue

        ver = int(ver[len(version) :])

        suffix = max(suffix, ver)

    if not (local or no_increment):
        suffix += 1

    suffix = max(suffix, 0)

    version = "{}{}".format(version, suffix)

    return version


def package_root(package: str, env):
    """Some of our older packages used the osx intermediate directory to avoid variants, whereas now we use platform variants.
    This function papers over the difference in structure"""
    root = env[f"REZ_{package.upper()}_ROOT"]
    osx = os.path.join(root, "osx")
    if os.path.exists(osx):
        return osx
    return root


def materialx_version():
    version = []
    with open(os.path.join(repo, "CMakeLists.txt")) as fp:
        for line in fp.readlines():
            if match := re.match("set\(MATERIALX_[A-Z]+_VERSION (?P<ver>\d+)\)", line):
                version.append(match.groupdict()["ver"])

    return version


def materialx_version_string():
    return ".".join(materialx_version())


def next_package_version(package_name):
    latest = latest_package_version(package_name)
    if latest is None:
        return 0

    return latest + 1


def latest_package_version(package_name):
    if not package_name.startswith("materialx"):
        package_name = "materialx" + package_name

    p = subprocess.Popen(
        ["rez-search", package_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = p.communicate()

    if err:
        return

    suffix = out.decode("utf-8").split("-a")[-1]
    if suffix:
        return int(suffix)

    return


def commit_hash():
    return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()


def variants():
    vars = list(config["variants"].items())
    vars.sort(key=lambda x: x[1]["id"])
    return vars


def variant_by_keys(keys):
    for variant in variants():
        if variant[1]["keys"] == keys:
            return variant


def rez_variant_list():
    vars = []
    for variant, data in variants():
        if not data.get("enabled", False):
            continue
        vars.append(data["keys"])

    return vars


def rez_package_source():
    return os.path.join(root, "package.py")


def requires(*exclude):
    requires = config["requires"]
    requires = [r for r in requires if not r.replace("!", "") in exclude]
    return requires


def build_requires(*exclude):
    build_requires = config["build_requires"]
    build_requires = [r for r in build_requires if not r.replace("!", "") in exclude]
    return build_requires


def cache_packages(packages):
    print("Caching {} ...".format(", ".join(packages)))
    commands = ["rez-env", "omnilauncher", "--", "rez-cache"] + list(packages)

    ret = subprocess.call(commands)
    if ret:
        raise RuntimeError("Failed to cache packages: {}".format(ret))
    print("Finished Caching packages.")
    return packages


def package_list(variant=None):
    variant = variant or {}
    full = requires() + build_requires() + variant["additions"] + variant["keys"]

    packages = collections.OrderedDict()
    for pack in full:
        if "!" in pack or "|" in pack:
            continue

        name = pack.split("-")[0]
        existing = packages.get(name)
        if existing:
            current_tokens = len(existing.split("-"))
            new_tokens = len(pack.split("-"))

            if new_tokens <= current_tokens:
                pack = existing

        packages[name] = pack

    order = list(packages.keys())
    priority = ["maya"]
    len_priority = len(priority)

    def sorter(x):
        x = x.split("-")[0]
        if x in priority:
            return priority.index(x)

        return order.index(x) + len_priority

    packages = sorted(packages.values(), key=lambda x: sorter(x))
    return packages


def exact_version():
    return []


def get_package_list_for(identifier, query=None):
    if not isinstance(identifier, dict):
        try:
            identifier = int(identifier)
        except:
            pass

        for name, variant in variants():
            if name == identifier:
                break
            if variant["alias"] == identifier:
                break
            if variant["id"] == identifier:
                break

        else:
            raise RuntimeError(
                "Could not find matching variant for {}".format(identifier)
            )
    else:
        variant = identifier

    from rez.resolved_context import ResolvedContext
    from rez.resolver import ResolverStatus

    context = ResolvedContext(package_list(variant))

    if context.status == ResolverStatus.failed:
        raise RuntimeError(
            f"Failed to create rez_env because: {context.failure_description}"
        )

    packages = []
    for package in context.resolved_packages:
        name = package.name
        version = package.version

        if query and name not in query:
            continue

        packages.append("{}-{}".format(name, version))

    return packages


def get_environment(request):
    if not request:
        raise RuntimeError("You need to pass a request to get a rez resolve")

    from rez.resolved_context import ResolvedContext
    from rez.resolver import ResolverStatus

    context = ResolvedContext(request)
    if context.status == ResolverStatus.failed:
        raise RuntimeError(
            f"Failed to create rez_env because: {context.failure_description}"
        )

    environ = context.get_environ()
    if "DEVELOPER_DIR" in os.environ:
        print("Found DEVELOPER_DIR. Adding to Rez environment.")
        environ["DEVELOPER_DIR"] = os.environ["DEVELOPER_DIR"]
    else:
        print("Did not find DEVELOPER_DIR. Not adding to Rez environment.")
    environ["XCODE_ATTRIBUTE_DEVELOPMENT_TEAM"] = "-"
    return environ


def get_environment_string(request=None, env=None):
    environ = env or get_environment(request)

    env_string = ""
    for key, val in environ.items():
        env_string += "{}={};".format(key, val)

    return env_string


def get_cmake_args(variant, root, request=None, env=None, exact_root=False):
    env = env or get_environment(request)

    if not exact_root:
        root = os.path.join(*([root] + variant["keys"]))

    py3 = env["REZ_PYTHON_MAJOR_VERSION"] == "3"

    usd_root = env.get("USD_ROOT") or env.get("OMNI_USD_ROOT")

    is_maya = bool(env.get("REZ_MAYA_ROOT"))
    build_extras = not is_maya

    if is_maya:
        pylib = (
            f"{package_root('maya', env)}/Applications/Autodesk/"
            "maya{REZ_MAYA_MAJOR_VERSION}/Maya.app/Contents/"
            "Frameworks/Python.framework/Versions/Current/lib/"
            "libpython{REZ_PYTHON_MAJOR_VERSION}.{REZ_PYTHON_MINOR_VERSION}.dylib"
        )

        pyexe = (
            f"{package_root('maya', env)}/Applications/Autodesk/"
            "maya{REZ_MAYA_MAJOR_VERSION}/Maya.app/Contents/"
            "bin/mayapy"
        )

        pyincl = (
            f"{package_root('maya', env)}/Applications/Autodesk/"
            "maya{REZ_MAYA_MAJOR_VERSION}/Maya.app/Contents/"
            "Frameworks/Python.framework/Versions/Current/"
            "include/python{REZ_PYTHON_MAJOR_VERSION}.{REZ_PYTHON_MINOR_VERSION}"
        )
    else:
        pylib = (
            f"{package_root('python', env)}/Python.framework/Versions/"
            "{REZ_PYTHON_MAJOR_VERSION}.{REZ_PYTHON_MINOR_VERSION}/"
            "lib/libpython{REZ_PYTHON_MAJOR_VERSION}.{REZ_PYTHON_MINOR_VERSION}.dylib"
        )
        pyexe = (
            f"{package_root('python', env)}/Python.framework/Versions/"
            "{REZ_PYTHON_MAJOR_VERSION}.{REZ_PYTHON_MINOR_VERSION}/"
            "bin/python{REZ_PYTHON_MAJOR_VERSION}"
        )
        pyincl = (
            f"{package_root('python', env)}/Python.framework/Versions/"
            "{REZ_PYTHON_MAJOR_VERSION}.{REZ_PYTHON_MINOR_VERSION}/"
            "/include/python{REZ_PYTHON_MAJOR_VERSION}.{REZ_PYTHON_MINOR_VERSION}"
        )

    args = {
        "CMAKE_OSX_ARCHITECTURES": ";".join(variant["architectures"]),
        "CMAKE_INSTALL_PREFIX": root,
        "CMAKE_BUILD_TYPE": "RelWithDebInfo",
        "MATERIALX_BUILD_PYTHON": build_extras,
        "MATERIALX_BUILD_VIEWER": build_extras,
        "MATERIALX_BUILD_SHARED_LIBS": True,
        "MATERIALX_PYTHON_EXECUTABLE": pyexe,
        "MATERIALX_BUILD_GRAPH_EDITOR": build_extras,
        "MATERIALX_BUILD_TESTS": False, # TODO: Remove this if/when the tests are fixed to work with the newer clang random lib
    }

    for k, v in args.items():
        if isinstance(v, six.string_types):
            v = v.format(**env)
        args[k] = v

    return args


def get_cmake_args_string(
    variant=None, request=None, env=None, args=None, root=None, exact_path=False
):
    args = args or get_cmake_args(
        variant=variant, root=root, request=request, env=env, exact_root=exact_path
    )

    return "\n".join(format_cmake_args(args))


def format_cmake_args(args):
    fmt = []
    for k, v in args.items():
        if isinstance(v, bool):
            v = str(v).upper()
        fmt.append("-D{}={}".format(k, v))

    return fmt


def find_cmake(path=None):
    path = path or os.environ["PATH"]
    for p in path.split(os.pathsep):
        cmake = os.path.join(p, "cmake")
        if os.path.exists(cmake):
            return cmake

    return "cmake"


def print_cmake_logs(path):
    paths = [
        # os.path.join(path, "CMakeFiles/CMakeOutput.log"),
        os.path.join(path, "CMakeFiles/CMakeError.log"),
    ]

    for p in paths:
        if not os.path.exists(p):
            print("Could not find:", p)
            continue

        with open(p) as fp:
            print("Printing Contents of {}:".format(p))
            print("\n\t".join(fp.readlines()))
            print("Finished Printing Contents of {}:".format(p))


def build_cmake(path, args, env, threads=None, xcrun=False):
    if not os.path.exists(path):
        print("Creating", path)
        os.makedirs(path)

    install_path = args["CMAKE_INSTALL_PREFIX"]
    if not os.path.exists(install_path):
        print("Creating", install_path)
        os.makedirs(install_path)

    if "DEVELOPER_DIR" in env or "DEVELOPER_DIR" in os.environ:
        print("Redirecting cmake output...")
        redirect = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    else:
        print("Not redirecting cmake output...")
        redirect = {}

    cmd = ["cmake", "-G", "Unix Makefiles", repo] + format_cmake_args(args)
    if xcrun:
        cmd.insert(0, "xcrun")
        print("Using xcrun to build Xcode Project")

    print("Generating build with \n", " ".join(cmd))
    proc = subprocess.Popen(cmd, cwd=path, env=env, **redirect)
    stdout, stderr = proc.communicate()
    ret = proc.returncode

    if stderr:
        print("\n\nstderr:\n\n {}".format(stderr.decode()))
    if stdout:
        print("\n\nstdout:\n\n {}".format(stdout.decode()))

    if ret != 0:
        print_cmake_logs(path)
        raise RuntimeError("Failed to generate project: {0}".format(ret))

    cmd = [
        "cmake",
        "--build",
        ".",
        "--config",
        args["CMAKE_BUILD_TYPE"],
        "--target",
        "install",
        "--",
        "-j",
        str(threads or multiprocessing.cpu_count()),
    ]
    print("Starting compilation...with args\n\n", " ".join(cmd))

    proc = subprocess.Popen(cmd, cwd=path, env=env, **redirect)
    stdout, stderr = proc.communicate()
    ret = proc.returncode

    if stderr:
        print("\n\nstderr:\n\n {}".format(stderr.decode()))
    if stdout:
        print("\n\nstdout:\n\n {}".format(stdout.decode()))

    if ret != 0:
        print_cmake_logs(path)
        raise RuntimeError("Failed to build: {0}".format(ret))

    print("Finished Build!")


def set_executable(path):
    print("Marking {} as executable".format(path))
    subprocess.check_output(["chmod", "+x", path])


@caffeinate
def build(
    variant,
    install_root,
    cache=True,
    print_args=False,
    exact_root=False,
    build_folder=None,
    threads=None,
    xcrun=False,
):
    packages = package_list(variant=variant)
    if cache:
        cache_packages(packages)

    env = get_environment(packages)
    args = get_cmake_args(variant, install_root, env=env, exact_root=exact_root)
    cmake = find_cmake(env.get("PATH"))

    print("Cmake", cmake)
    if print_args:
        print("Environment:\n\n", get_environment_string(env=env), "\n\n")
        print("CMake:\n\n", get_cmake_args_string(args=args), "\n\n")
        return

    if not build_folder:
        build_folder = os.path.join(
            root, "build/materialx_build_{}".format(variant["alias"])
        )

    print("Building in ", build_folder)
    build_cmake(build_folder, args, env, threads=threads, xcrun=xcrun)

    print("All done.")


def build_variant_name(
    name,
    install_root,
    cache=True,
    print_args=False,
    exact_root=False,
    build_folder=None,
    threads=None,
    xcrun=False,
):
    variant = None
    vars = variants()
    for v, data in vars:
        if v == name:
            variant = v, data
            break

    if not variant:
        print("Could not find variant by name. Searching for alias.")
        for v, data in vars:
            if data["alias"] == name:
                variant = v, data
                break

    if not variant:
        raise RuntimeError("Could not find a matching variant for : {}".format(name))

    name, data = variant
    print("Building {}".format(name))

    return build(
        data,
        install_root,
        cache=cache,
        print_args=print_args,
        exact_root=exact_root,
        build_folder=build_folder,
        threads=threads,
        xcrun=xcrun,
    )


def build_variant_id(
    index,
    install_root,
    cache=True,
    print_args=False,
    exact_root=False,
    build_folder=None,
    threads=None,
    xcrun=False,
):
    for name, data in variants():
        if data["id"] != index:
            continue
        print("Building {}".format(name))

        return build(
            data,
            install_root,
            cache=cache,
            print_args=print_args,
            exact_root=exact_root,
            build_folder=build_folder,
            threads=threads,
            xcrun=xcrun,
        )
    else:
        raise RuntimeError("Could not find variant with matching ID")


def check_local_links(path, ignore=None):
    ignore = ignore or []
    links = subprocess.check_output(["otool", "-L", path]).decode("utf-8").split("\n")
    errors = set()
    for line in links:
        line = line.strip()
        if not line:
            continue
        if line.startswith("@"):
            continue
        if line.startswith("/usr/lib/"):
            continue
        if line.startswith("/usr/local/apps"):
            continue
        if line.startswith("/System/Library/"):
            continue

        do_ignore = False
        for ig in ignore:
            if line.startswith(ig):
                do_ignore = True
                break

        if do_ignore:
            continue

        errors.add(line)

    return errors


def fix_mod(path, old_path, new_path, variant):
    print(f"Fix Mod: {path} -- {old_path} || {new_path}")
    variant_keys = os.path.sep.join(variant["keys"])

    with open(path, "r") as fp:
        lines = fp.readlines()

    write = False
    for i, line in enumerate(lines):
        new_line = line.replace(old_path, new_path)

        # Fix duplication error that can occur with simple replace
        if variant_keys in new_line:
            tokens = new_line.split(variant_keys)
            pre = tokens[0]
            post = tokens[-1]
            new_line = f"{pre}{variant_keys}{post}"

        if line != new_line:
            write = True

            print(lines[i], "\n\t--->\n\t\t", new_line, "\n")
            lines[i] = new_line

    if not write:
        print("No requirement to modify", path)
        return

    print("Modifying", path)
    with open(path, "w") as fp:
        fp.writelines(lines)

    print("Done modifying", path)


def add_rpath(lib, rpath):
    subprocess.call(["/usr/bin/install_name_tool", "-add_rpath", rpath, lib])


def sign(lib):
    ret = subprocess.call(
        [
            "codesign",
            "-s",
            "-",
            "--force",
            "--deep",
            "--preserve-metadata=entitlements,identifier",
            lib,
        ]
    )
    if ret:
        raise RuntimeError("Could not codesign the library : {}".format(ret))


def fix_rpaths(start, destination, index):
    for variant in variants():
        v, d = variant
        if d["id"] == index:
            break
    else:
        raise RuntimeError("Failed to find variant with id {} to fix".format(index))

    variant_root = os.path.join(*([destination] + variant[1]["keys"]))
    variant_lib_root = os.path.join(variant_root, "lib")

    print(
        "Fixing rpaths under {} to {} with {}".format(start, destination, variant_root)
    )

    libs = set()
    bins = set()
    pys = set()
    mods = set()

    for root, dirs, files in os.walk(start):
        if root.endswith("/bin"):
            for f in files:
                file_path = os.path.join(root, f)
                if not os.access(file_path, os.X_OK):
                    continue

                ftype = subprocess.check_output(["file", file_path]).decode("utf-8")
                if "ASCII" in ftype:
                    pys.add(file_path)
                else:
                    bins.add(file_path)

        for f in files:
            _, ext = os.path.splitext(f)
            if ext in (".dylib", ".so", ".bundle"):
                file_path = os.path.join(root, f)
                libs.add(file_path)

            elif ext == ".mod":
                file_path = os.path.join(root, f)
                mods.add(file_path)

    for mod in mods:
        fix_mod(mod, start, variant_root, variant[1])

    errors = {}
    for artifact in libs | bins:
        add_rpath(artifact, variant_lib_root)
        sign(artifact)
        errs = check_local_links(artifact, ignore=[start])
        if errs:
            errors[artifact] = errs

    if errors:
        print("Failed to remove external links...")
        pprint.pprint(errors)
        raise RuntimeError("Failed to remove external links")

    print("Completed fixing rpaths!")


def get_cache_path():
    if not os.getenv("REZ_OMNILAUNCHER_ROOT"):
        print("Finding precache root from omnilauncher")
        cmd = [
            "rez-env",
            "omnilauncher",
            "pyside2",
            "--",
            "python3",
            "-c",
            "import omnilauncher.env.settings as s;print('PRECACHE_ROOT IS', s.get_setting('PRECACHE_ROOT'))",
        ]
        ret = subprocess.check_output(cmd).decode("utf-8")
        for line in ret.split("\n"):
            if line.startswith("PRECACHE_ROOT IS"):
                ret = line.split()[-1]
                break

        else:
            raise RuntimeError("Could not find PRECACHE_ROOT")
    else:
        import omnilauncher.env.settings

        ret = omnilauncher.env.settings.get_setting("PRECACHE_ROOT")

    print(f"Cache path is {ret}")
    return ret.strip()


def make_package(
    dest=None, name=None, version=None, release=False, paths=None, cache_path=False
):
    if not dest:
        print("Making temporary destination for package release")
        dest = tempfile.mkdtemp()

    template = os.path.join(root, "package.py")
    with open(template, "r") as fp:
        lines = fp.readlines()

    cache_dir = "/usr/local/apps/"
    if dest.startswith(cache_dir):
        tokens = os.path.split(dest[len(cache_dir) :])
        name = name or tokens[0]
        version = version or tokens[1]
    else:
        branch = branch_name()
        name = name or package_name(branch=branch)
        version = version or package_version(branch=branch)

    variant_list = []
    paths = paths or [dest]
    if cache_path:
        cache_path = get_cache_path()
        paths = [os.path.join(cache_path, name, version)]

    for variant, data in variants():
        for search_path in paths:
            tokens = [search_path] + data["keys"] + ["README.md"]
            readme = os.path.join(*tokens)

            tokens = [search_path] + data["keys"] + ["bundled_precache_files.zip"]
            precache = os.path.join(*tokens)

            if os.path.exists(precache) or os.path.exists(readme):
                variant_list.append(data["keys"])
                print("Found variant {}".format(variant))
            else:
                print(
                    "Could not find variant: {}. Not adding to list. Searched in:\n\t{}\n\t{}".format(
                        variant, readme, precache
                    )
                )

    if not variant_list:
        raise RuntimeError("Could not find any variants. Aborting build.")

    keys = {
        "PACKAGE_NAME": name,
        "PACKAGE_VERSION": version,
        "REQUIRES": requires(name),
        "TIMESTAMP": int(time.time()),
        "COMMIT_HASH": commit_hash(),
        "VARIANT_LIST": variant_list,
    }

    new = []
    orez = re.compile("#.*orez-([a-z]+)(:.)?([a-zA-Z_0-9]+)?")
    for line in lines:
        match = orez.search(line)
        if not match:
            new.append(line)
            continue

        cmd, _, key = match.groups()

        if cmd == "rm":
            continue

        var = line.split("=")[0].rstrip()
        val = keys.get(key, key)
        if isinstance(val, six.string_types):
            val = '"{}"'.format(val)
        elif isinstance(val, list):
            var_len = len(var)
            val = pprint.pformat(val, indent=var_len + 4, width=120 - var_len)
            if "\n" in val:
                val = "[\n" + val[1:-1] + "\n{}]".format(" " * var_len)

        line = "{} = {}\n".format(var, val)

        if key not in keys:
            print("Missing key:", key)

        new.append(line)

    if not os.path.exists(dest):
        os.makedirs(dest)
    with open(os.path.join(dest, "package.py"), "w") as fp:
        fp.writelines(new)

    if not release:
        print("Release was not selected.")
        return

    print("Releasing package")
    command = [
        "rez-env",
        "omnilauncher",
        "--",
        "rez-deploy",
        "--package",
        name,
        "--version",
        version,
        "--manifest_only",
    ]
    if "REZ_OMNILAUNCHER_ROOT" in os.environ:
        command = command[3:]

    print(" ".join(command))
    ret = subprocess.call(command, cwd=dest)
    if ret:
        raise RuntimeError("Failed to release package!")

    print("Released package")

    print("About to create tag...")
    try:
        tag_release(version)
    except Exception as e:
        print(f"Error: Failed to tag {version} because {traceback.format_exc(e)}")

    print("Completed package release process. Hopefully everything worked????")


def tag_release(version):
    cwd = os.path.dirname(__file__)
    print(f"Starting tag creation in {cwd}")

    from rez import release_vcs

    vcs = release_vcs.create_release_vcs(cwd)

    print(f"Using VCS: {vcs}")
    ret = vcs.create_release_tag(
        version, message=f"Automated tag from Jenkins build: {version}"
    )

    print(f"Tried to create tag: {version} with status {ret}")


def release_precache(index, root, name=None, version=None):
    for variant, data in variants():
        if data["id"] == index:
            break
    else:
        raise RuntimeError("No matching variant for id {}".format(index))

    name = name or package_name()
    version = version or package_version()

    tokens = [get_cache_path()] + [name, version] + data["keys"]
    precache = os.path.join(*tokens)
    print("Checking {} for existing cache.".format(precache))
    if os.path.exists(precache):
        print(
            "Removing existing precache at {} to replace with shiny new one.".format(
                precache
            )
        )
        shutil.rmtree(precache)

    print(
        "Releasing {}-{} with variant: {} from: {}".format(name, version, variant, root)
    )

    command = [
        "rez-env",
        "omnilauncher",
        "--",
        "rez-deploy",
        "--package",
        name,
        "--version",
        version,
    ]
    for k in data["keys"]:
        command.extend(["-v", k])

    print(" ".join(command))

    ret = subprocess.call(command, cwd=root)
    if ret:
        raise RuntimeError("Failed to create precache!")

    if not os.path.exists(precache):
        raise RuntimeError("Failed to find precache at {}".format(precache))

    print("Created precache at {}".format(precache))


def get_xcode_data():
    data = {}
    cmd = ["xcodebuild", "-version", "-sdk"]
    version = subprocess.check_output(cmd).decode("utf-8").split("\n")[-2].split()[-1]

    cmd.append("-json")
    sdks = subprocess.check_output(cmd).decode("utf-8")

    for sdk in json.loads(sdks):
        if not sdk.get("isBaseSdk"):
            continue
        display = sdk.get("displayName")
        build = sdk.get("productBuildVersion")
        if not build:
            continue

        data[display] = build

    remove = []
    for key in data.keys():
        if "Simulator" in key or "(" in key:
            remove.append(key)
            continue

        if "{} Internal".format(key) in data:
            remove.append(key)
            continue

    for r in remove:
        data.pop(r)

    data["Xcode"] = version
    return data


def should_use_xcrun():
    data = get_xcode_data()
    xcode = int(data["Xcode"][:2])
    cmake_ver = int(os.environ.get("REZ_CMAKE_MINOR_VERSION", 0))

    sdk_ver = None
    for k, v in data.items():
        if k.startswith("macOS"):
            sdk_ver = int(v[:2])

    if not sdk_ver:
        # If we can't find the SDK ver, then Xcode isn't setup properly, so don't use xcrun to run cmake
        return False

    if xcode >= 14:
        # if it's above 13, it ships with patches to CMake to find the SDK it looks like so xcrun is required
        return True

    if sdk_ver >= 22 and cmake_ver < 25:
        # If the SDK version is higher than 21/Star, CMake before version 25 will not know how to find the SDK properly
        return True

    # Otherwise we default to using the Rez supplied CMake
    return False


def parse_boolean(val):
    """
    :type val: str
    """
    val = val.lower()
    for x in ("y", "1", "t", "o"):
        if val.startswith(x):
            return True

    return False


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="commands", dest="command")

    _version = subparsers.add_parser("version")
    _version.add_argument(
        "-n", "--next", help="Get the next version to create", action="store_true"
    )
    _version.add_argument(
        "-l", "--latest", help="Get the current latest version", action="store_true"
    )
    _version.add_argument("-p", "--package_name", help="The package name to look for")

    subparsers.add_parser("variants")

    _build = subparsers.add_parser("build")
    _build.add_argument(
        "-n", "--name", help="Name of the variant to build", nargs="*", type=str
    )
    _build.add_argument(
        "-i", "--index", help="Index of the variant to use", nargs="*", type=int
    )
    _build.add_argument("-r", "--root", help="Root to install under", type=str)
    _build.add_argument(
        "-e",
        "--exact_root",
        help="Use the root dir as an exact output dir",
        action="store_true",
    )
    _build.add_argument(
        "-c", "--no_cache", help="Disables cache checks", action="store_true"
    )
    _build.add_argument(
        "-p",
        "--print_args",
        help="Print arguments to configure CMake or other build systems",
        action="store_true",
    )
    _build.add_argument(
        "-b",
        "--build",
        help="The build folder. If one doesn't exist, it will create one in the cwd",
        type=str,
    )
    _build.add_argument(
        "-j",
        "--jobs",
        help="The number of job threads to run",
        default=multiprocessing.cpu_count(),
    )
    _build.add_argument(
        "-x",
        "--xcrun",
        help="Whether to use xcrun or not. Accepts a boolean string",
        type=str,
        default=str(should_use_xcrun()),
    )

    _rpath = subparsers.add_parser("fix_rpath")
    _rpath.add_argument("-r", "--root", help="The current package root", type=str)
    _rpath.add_argument(
        "-i", "--index", help="The variant index to fix with", type=int, required=True
    )
    _rpath.add_argument(
        "-d", "--destination", help="The new package root", type=str, required=True
    )

    _package = subparsers.add_parser("package")
    _package.add_argument("-r", "--root", help="The root of the package", type=str)
    _package.add_argument(
        "-n", "--name", help="The name of the package to release under"
    )
    _package.add_argument("-v", "--version", help="The version string to release as")
    _package.add_argument(
        "--release", action="store_true", help="Whether to release or not"
    )
    _package.add_argument(
        "-p", "--path", nargs="*", help="A list of paths to look under for variants"
    )
    _package.add_argument(
        "-c", "--cache_path", action="store_true", help="Look under cached paths"
    )

    _release = subparsers.add_parser("release")
    _release.add_argument("-r", "--root", help="The path to release from")
    _release.add_argument(
        "-i", "--index", help="The index of the variant to release", type=int
    )
    _release.add_argument(
        "-n", "--name", help="The name of the package to release under"
    )
    _release.add_argument("-v", "--version", help="The version string to release as")

    args = parser.parse_args()

    cmd = args.command
    if cmd == "version":
        if args.next:
            print(next_package_version(args.package_name))
        elif args.latest:
            print(latest_package_version(args.package_name) or 0)
        else:
            print(materialx_version_string())
    elif cmd == "variants":
        pprint.pprint(variants())
    elif cmd == "fix_rpath":
        fix_rpaths(start=args.root, destination=args.destination, index=args.index)
    elif cmd == "package":
        make_package(
            dest=args.root,
            name=args.name,
            version=args.version,
            release=args.release,
            paths=args.path,
            cache_path=args.cache_path,
        )
    elif cmd == "release":
        release_precache(
            index=args.index, root=args.root, name=args.name, version=args.version
        )
    elif cmd == "build":
        use_xcrun = parse_boolean(args.xcrun)
        print("OS Version: ", subprocess.check_output(["sw_vers"]))
        cmake_command = ["cmake", "--version"]
        if use_xcrun:
            print("Using XCrun")
            cmake_command.insert(0, "xcrun")

        print("CMake Version: ", subprocess.check_output(cmake_command))
        print("XCode:", subprocess.check_output(["xcode-select", "-p"]))
        print(
            "XCode SDKS:\n",
            pprint.pformat(get_xcode_data())
            .replace("{", "")
            .replace("}", "")
            .replace("'", "")
            .strip(),
        )
        print("SIP Status:\n", subprocess.check_output(["csrutil", "status"]))
        print("Python executable:", sys.executable)
        kwargs = {
            "cache": not args.no_cache,
            "print_args": args.print_args,
            "exact_root": args.exact_root,
            "build_folder": args.build,
            "threads": args.jobs,
            "xcrun": use_xcrun,
        }
        if args.name:
            for name in args.name:
                build_variant_name(name, args.root, **kwargs)
        elif args.index != None:
            for index in args.index:
                build_variant_id(index, args.root, **kwargs)
        else:
            raise RuntimeError("Not enough arguments to build this")
    else:
        print("ERROR: Unknown argument.")


def bootstrap():
    args = sys.argv[1:]
    command = [
        "rez-env",
        "python-3",
        "six",
        "rez-2",
        "cmake",
        "--",
        "python3",
        os.path.abspath(__file__),
    ]
    print("Running outside rez. Launching with bootstrap:\n", " ".join(command))
    command.extend(args)

    ret = subprocess.call(command)
    sys.exit(ret)


if __name__ == "__main__":
    needs_rez = ["build", "package"]
    needs_rez = any((b in sys.argv) for b in needs_rez)
    needs_rez = needs_rez and (
        "REZ_REZ_ROOT" not in os.environ or "REZ_CMAKE_ROOT" not in os.environ
    )
    if needs_rez:
        bootstrap()
    else:
        main()
