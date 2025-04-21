#!/bin/bash

#
# # Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


set -x

if [ $# -lt 1 ]; then
    echo "Error: Please provide required arguments."
    echo "Usage: $0 <directory> [is_docker]"
    exit 1
fi

DEST_DIR="$1"
IS_DOCKER="${2:-false}"  # default is false

if [ ! -d "$DEST_DIR" ]; then
    echo "Error: Directory '$DEST_DIR' does not exist."
    exit 1
fi

SCRIPT_DIR=$DEST_DIR
cd "$SCRIPT_DIR"

if [ -f "setup_pypath.sh" ]; then
    source setup_pypath.sh
else
    echo "Warning: setup_pypath.sh not found in the current directory."
fi

python3 deploy_py/main.py -deploy --is-docker "$IS_DOCKER"
if [ $? -ne 0 ]; then
    echo "Error: Deployment failed."
    exit 1
fi

echo "Deployment completed successfully."
