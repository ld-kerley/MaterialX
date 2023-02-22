#!/usr/bin/env groovy
// Import tdg library from https://stash.sd.apple.com/projects/TDGIN/repos/ci.library/browse
@Library("tdg_ci") __
@Library("omni_jenkins_utils") _

def USD_VERSION = ""
def USD_REQUIRES = ""
def LATEST_PACKAGE = ""
def NEXT_PACKAGE = ""
def CURRENT_TIME = ""
def XCODE_DIR = null

def totally = null
def TOTALLY_LIB = 'reality-tools/Jenkins/totally.groovy'

def XIA_IMAGE_NAME = "Xcode12E5244b_m20E205_i18E173_FastSim_Boost_42GB.dmg"



def setup = {
    omniSetup()

    echo "Installing XCode"
    dir ('reality-tools'){
      git url: 'ssh://git@stash.sd.apple.com/tdgui/retools.git', branch: 'release/glazul'
    }
    sudo("pip install virtualenv")
    totally = load TOTALLY_LIB

    totally.buildEnvironmentSetup()

    // Mount up XCode and select it as default.
    XCODE_DIR = totally.attachXcode(XIA_IMAGE_NAME, ["/TDG/TDG-SW/Teams/Tools/XIA/jenkins-xia-images", "/Volumes/TDG-SW/Teams/Tools/XIA/jenkins-xia-images"])
    totally.updateXBSBundle()

    echo "Reconnecting to Omni to make sure we don't disconnect half way through the build"
    omniConnect()
}

def get_version = {
  // Get the MaterialX version from the utils script
  script {
    MaterialX_VERSION = sh (
      script: '''
        python3 $WORKSPACE/apple/build_scripts/utils.py version
      ''',
      returnStdout: true
    ).trim()

    echo "Found Version ${MaterialX_VERSION} for materialx-${GIT_BRANCH}-${MATERIALX_VERSION}-a"
    if (!MATERIALX_VERSION?.trim()) {
      error("Failed getting the MaterialX version for the Rez package")
    }

    echo "Checking for latest version of materialx-${GIT_BRANCH}-${MATERIALX_VERSION}-a"
    LATEST_PACKAGE = sh (
       script: """
         python3 $WORKSPACE/apple/build_scripts/utils.py version --latest -p materialx-${GIT_BRANCH}-${MATERIALX_VERSION}-a
       """,
       returnStdout: true
     ).trim()

    echo "Latest materialx-${GIT_BRANCH}-${MATERIALX_VERSION}-a package found is ${LATEST_PACKAGE}"
    if (!LATEST_PACKAGE?.trim()) {
      error("Failed getting the latest version for the Rez package")
    }

    // Get Next Package Version
    NEXT_PACKAGE = sh (
      script: """
        python3 $WORKSPACE/apple/build_scripts/utils.py version --next -p materialx-${GIT_BRANCH}-${MATERIALX_VERSION}-a
      """,
      returnStdout: true
    ).trim()

    if (params.CUSTOM_VERSION?.trim()) {
        NEXT_PACKAGE = params.CUSTOM_VERSION.trim()
        echo "Using custom version: ${NEXT_PACKAGE}"
    }
  }
}

def build = {
  script {
      withEnv(["DEVELOPER_DIR=$XCODE_DIR"]) {
        if (params.CLEAN_BUILD) {
          sh 'if [ -d "$WORKSPACE/$BUILD_FOLDER/build" ]; then rm -Rf $WORKSPACE/$BUILD_FOLDER/build; fi'
          sh 'if [ -d "$WORKSPACE/$BUILD_FOLDER/inst" ]; then rm -Rf $WORKSPACE/$BUILD_FOLDER/inst; fi'
          sh 'if [ -d "$WORKSPACE/$BUILD_FOLDER/src" ]; then rm -Rf $WORKSPACE/$BUILD_FOLDER/src; fi'
          sh 'if [ -f "$WORKSPACE/CMakeCache.txt" ]; then rm $WORKSPACE/CMakeCache.txt; fi'
          sh 'if [ -d "$WORKSPACE/CMakeFiles" ]; then rm -Rf $WORKSPACE/CMakeFiles; fi'
        }
        sh 'mkdir -p $WORKSPACE/$BUILD_FOLDER/build'
        sh 'mkdir -p $WORKSPACE/$BUILD_FOLDER/inst'
        sh 'mkdir -p $WORKSPACE/$BUILD_FOLDER/src'
        sh 'export'
        sh 'xcode-select --print-path'

        script {
                withEnv(["DEVELOPER_DIR=$XCODE_DIR", "PATH+REZ=$OMNI_PACKAGE_CACHE_ROOT/rez/_core/2.18.0-a0/osx/bin/rez"]) {
                    sh '''
                    rez-env rez-2 six cmake python-3 -- python3 $WORKSPACE/apple/build_scripts/utils.py build -i $USD_VARIANT_ID -r $WORKSPACE/$BUILD_FOLDER/inst -j 12
                        '''
                }
            }
    }
  }
}

def test = {
  script {
    withEnv(["DEVELOPER_DIR=$XCODE_DIR", "PATH+EXTRA=$WORKSPACE/$BUILD_FOLDER/inst/bin","PYTHONPATH+REZ=$WORKSPACE/$BUILD_FOLDER/inst/lib/python","USD=$WORKSPACE/$BUILD_FOLDER/inst"]) {
      if (params.RUN_TESTS) {
        sh '''
          cd $WORKSPACE/$BUILD_FOLDER/build
          rez-env $USD_REQUIRED_PACKAGES $PYTHON_USD_PACKAGES -- ctest -T test -C Release -j 1 
        '''
      }
    }
  }
}

def fix_rpaths = {
  script {
    withEnv(["DEVELOPER_DIR=$XCODE_DIR", "PATH+EXTRA=$WORKSPACE/$BUILD_FOLDER/inst/bin","PYTHONPATH+REZ=$WORKSPACE/$BUILD_FOLDER/inst/lib/python","USD=$WORKSPACE/$BUILD_FOLDER/inst"]) {

      if (!LATEST_PACKAGE?.trim() || !MATERIALX_VERSION.trim() || !NEXT_PACKAGE.trim()) {
        get_version()
      }

      echo "Latest ${USD_PACKAGE_NAME} package found is: ${LATEST_PACKAGE}"
      if (!LATEST_PACKAGE?.trim()) {
        error("Failed getting the latest version for the Rez package")
      }

      echo "MaterialX Version found is: ${MATERIALX_VERSION}"
      if (!MATERIALX_VERSION?.trim()) {
        error("Failed getting the latest MaterialX Version")
      }

      echo "Next Package Counter is: ${NEXT_PACKAGE}"
      if (!NEXT_PACKAGE?.trim()) {
        error("Failed getting the next package counter for the Rez package")
      }


      sh """
        cd $WORKSPACE
        USD_PACKAGE_VERSION="${GIT_BRANCH}-${MATERIALX_VERSION}-a${NEXT_PACKAGE}"

        echo "Fix MaterialX Rpaths"
        rez-env python-3 -- python3 $WORKSPACE/apple/build_scripts/utils.py fix_rpath -r "$WORKSPACE/$BUILD_FOLDER/inst" -d "$OMNI_PACKAGE_CACHE_ROOT/${USD_PACKAGE_NAME}/\${USD_PACKAGE_VERSION}/" -i $USD_VARIANT_ID
      """
    }
  }
}


def release = {
  script {
    withEnv(["DEVELOPER_DIR=$XCODE_DIR", "PATH+EXTRA=$WORKSPACE/$BUILD_FOLDER/inst/bin","PYTHONPATH+REZ=$WORKSPACE/$BUILD_FOLDER/inst/lib/python","USD=$WORKSPACE/$BUILD_FOLDER/inst"]) {

      if (!LATEST_PACKAGE?.trim() || !MATERIALX_VERSION.trim() || !NEXT_PACKAGE.trim()) {
        get_version()
      }

      echo "Latest ${USD_PACKAGE_NAME} package found is: ${LATEST_PACKAGE}"
      if (!LATEST_PACKAGE?.trim()) {
        error("Failed getting the latest version for the Rez package")
      }

      echo "MaterialX Version found is: ${MATERIALX_VERSION}"
      if (!MATERIALX_VERSION?.trim()) {
        error("Failed getting the latest MaterialX Version")
      }

      echo "Next Package Counter is: ${NEXT_PACKAGE}"
      if (!NEXT_PACKAGE?.trim()) {
        error("Failed getting the next package counter for the Rez package")
      }


      if (params.REZ_RELEASE) {
        if (!CURRENT_TIME?.trim()) {
          CURRENT_TIME = sh (
            script: """
              echo \$(date '+%s')
            """,
            returnStdout: true
          ).trim()
        }

        script {
            withEnv(["DEVELOPER_DIR=$XCODE_DIR", "PATH+REZ=$OMNI_PACKAGE_CACHE_ROOT/rez/_core/2.18.0-a0/osx/bin/rez"]) {
                sh """
                    python3 $WORKSPACE/apple/build_scripts/utils.py release -i $USD_VARIANT_ID -r $WORKSPACE/$BUILD_FOLDER/inst --name materialx --version ${GIT_BRANCH}-${MATERIALX_VERSION}-a${NEXT_PACKAGE}
                """
            }
        }
      }
    }
  }
}


// Release the USD package.py
def make_package = {
  setup()
  script {
      withEnv(["DEVELOPER_DIR=$XCODE_DIR", "PATH+EXTRA=$WORKSPACE/$BUILD_FOLDER/inst/bin","PYTHONPATH+REZ=$WORKSPACE/$BUILD_FOLDER/inst/lib/python"]) {

        if (!LATEST_PACKAGE?.trim()) {
          get_version()
        }

        echo "Latest ${USD_PACKAGE_NAME} package found is ${LATEST_PACKAGE}"
        if (!LATEST_PACKAGE?.trim()) {
          error("Failed getting the latest version for the Rez package")
        }

        if (params.REZ_RELEASE) {
          script {
            withEnv(["DEVELOPER_DIR=$XCODE_DIR", "PATH+REZ=$OMNI_PACKAGE_CACHE_ROOT/rez/_core/2.18.0-a0/osx/bin/rez"]) {
                sh """
                    echo "Release Package Version: ${GIT_BRANCH}-${MATERIALX_VERSION}-a${NEXT_PACKAGE}"
                    cd $WORKSPACE
                    git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
                    git fetch --all
                    git branch --set-upstream-to=origin/${GIT_BRANCH} ${GIT_BRANCH}
                    python3 $WORKSPACE/apple/build_scripts/utils.py package -r $WORKSPACE/$BUILD_FOLDER/inst --name materialx --version ${GIT_BRANCH}-${MATERIALX_VERSION}-a${NEXT_PACKAGE} -c --release
                """
            }
          }
        }
      }
    }
}


pipeline {
  agent none
  options {
    disableConcurrentBuilds()
    throttle(['LimitPerNode'])
  }
  parameters {
    separator(name: "OPTIONS_SEP", sectionHeader: "Build Options:")
    booleanParam(name: 'CLEAN_BUILD', defaultValue: true, description: "Wipe any existing build folders to make sure it builds from scratch. Set to False to make testing unit tests faster.")
    booleanParam(name: 'RUN_TESTS', defaultValue: false, description: "Whether to run Unit Tests or not, should only be used for testing purposes.")
    booleanParam(name: 'REZ_RELEASE', defaultValue: true, description: "Whether to release the package to Rez.")
    string(name: 'CUSTOM_VERSION', defaultValue: '', description: "Use a custom version suffix for this build.")
    separator(name: "BUILD_VERSIONS_SEP", sectionHeader: "Choose Versions To Build:")
    booleanParam(name: 'BUILD_PYTHON39', defaultValue: true, description: "Build Python 3.9 variant")
    booleanParam(name: 'BUILD_MAYA', defaultValue: true, description: "Whether to try building USD for Maya")
  }
  environment {
    NUMBER_CORES = "8"
    OMNI_REZ_PIPELINE_ROOT = "/Volumes/TDG-CCT/pipeline"
    OMNI_PACKAGE_CACHE_ROOT = "/usr/local/apps"
    USD_REQUIRED_PACKAGES = "python-3"
    REZ_CONFIG_FILE = '/Volumes/TDG-CCT/pipeline/config/rez/rezconfig-dev.py'
    TDG_CCT_LINKED_DIR = '/TDG/TDG-CCT'
    SZ_BRANCH = 'master'  //  Required for XCode / RETools mounting
  }

  stages {
    stage("Build MaterialX") {
      parallel {


        stage('Python 3.9') {
          agent { label 'omni_arm' }
          when {
            expression { params.BUILD_PYTHON39 == true }
          }
          environment {
            USD_VARIANT_ID = "0"
            PYTHON_USD_PACKAGES = 'python-3 usd_tdg-release'
            BUILD_FOLDER = 'MaterialXPython39'
            USD_PACKAGE_NAME = 'materialx'
            OS_VARIANT = 'platform-osx'
          }
          stages {
            stage('Core') {
              stages {
                stage('Setup Python 3.9') {
                  steps {script {setup()}}
                }
                stage('Build') {
                  steps {script {build()}}
                }
                stage('Test'){
                  steps {script {test()}}
                }
                stage('Fix Rpaths'){
                  steps {script {fix_rpaths()}}
                }
                stage('Release'){
                  steps {script {release()}}
                }
              }
            }
          }
          post {
                cleanup {
                    script {
                        totally.cleanUp()
                    }
                }
          }
        }

        stage('Maya') {
          agent { label 'omni_arm' }
          when {
            expression { params.BUILD_MAYA == true }
          }
          environment {
            USD_VARIANT_ID = "1"
            PYTHON_USD_PACKAGES = 'usd_tdg-release'
            BUILD_FOLDER = 'MaterialXMaya'
            USD_PACKAGE_NAME = 'materialx'
            OS_VARIANT = 'platform-osx'
          }
          stages {
            stage('Core') {
              stages {
                stage('Setup Maya') {
                  steps {script {setup()}}
                }
                stage('Build') {
                  steps {script {build()}}
                }
                stage('Test'){
                  steps {script {test()}}
                }
                stage('Fix Rpaths'){
                  steps {script {fix_rpaths()}}
                }
                stage('Release'){
                  steps {script {release()}}
                }
              }
            }
          }
          post {
                cleanup {
                    script {
                        totally.cleanUp()
                    }
                }
          }
        }


      }
    }
    stage("Package") {
      agent { label 'omni_arm' }
      when {
        expression { params.REZ_RELEASE == true }
      }
      environment {
          USD_ADDITIONAL_PACKAGES = 'python-3'
          BUILD_FOLDER = 'USDPackage'
          PYTHON_LOCATION = 'osx'
          PYTHON_EXECUTABLE = 'osx/Python.framework/Versions/2.7/bin/python'
          PYTHON_LIBRARY = 'osx/Python.framework/Versions/2.7/lib/libpython2.7.dylib'
          USD_PACKAGE_NAME = 'usd'
          PYTHON_USD_PACKAGES = 'python-2.7.15-a4 usd_tdg-release'
      }
      steps {script {make_package()}}
    }
  }
}
