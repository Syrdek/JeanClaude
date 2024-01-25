#!/bin/bash

export PYTHON="python3.10"
export http_proxy="http://int59:3128"
export https_proxy="http://int59:3128"
export CMAKE_ARGS="-DLLAMA_AVX2=OFF -DLLAMA_F16C=ON -DLLAMA_FMA=OFF"
export FORCE_CMAKE=1
export USE_NNPACK=0
export PIP="$PYTHON -m pip --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org --proxy='192.168.0.59:3128'"

test 
test -d venv || $PYTHON -m venv venv
. venv/bin/activate
$PIP install pip
$PIP install -r requirements.txt

