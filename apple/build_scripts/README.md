# Omni Maya USD Setup

The setup here will handle both `local` and `CI` builds of Maya USD.

The build logic is set in the `utils.py` and the configuration is under `config.json`.
Orchestration is handled by `rez` or `jenkins`.

## Instructions

### Local Rez Build

To build locally using Rez, run the following commands.
This will build all variants that are marked as `enabled` in the config file.

1. `cd <usd>/apple/build` where `<usd>` is the root of this repo
2. `rez-build --install --prefix=/usr/local/apps`

### Local CMake Build

You may want to develop locally and build as part of that process.
To get the necessary variables to configure your CMake project, run the following command:

`python utils.py build -i <variant_index> -r <build_location> -p`

An example to get the settings for variant `0` is below.

`python3 utils.py build -i 2  -r /usr/local/apps/maya_usd/local-0.21.0-a0 -p `.

To break the command down:

* `-i 2` uses the Configuration with ID 2 (at this point it's Maya 2023)
* `-r /usr/local/apps/maya_usd/local-0.21.0-a0` says where to build it
* `-p` says to print the variables and then exit

This will do the following:

* Cache all requirements for the given variant
* Print out the Environment Variables needed
* Print out the CMake build arguments needed

You can then take these and put it into your IDE of choice.

### CI Build

Go to `https://jenkins08.muse.apple.com/job/USD/job/Maya-USD/` and select a branch/PR to build.
Then simply build and watch it go.

## utils.py

The brains behind the operation is the `utils.py` command

The command has multiple options. Run `--help` with it to learn more about what it can do.
