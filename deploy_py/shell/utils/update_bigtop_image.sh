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


###########################################
# Apache Bigtop Base Image Update Script
###########################################
# 
# Purpose:
#   This script updates Apache Bigtop base Docker images to support Ambari-based 
#   big data cluster deployment. Apache Bigtop provides a unified way to package 
#   and install Hadoop ecosystem components, while Ambari offers cluster management
#   and monitoring capabilities.
#
# Background:
#   - Apache Bigtop: An Apache Foundation project for packaging and testing 
#     big data components (Hadoop, Spark, HBase, etc.)
#   - Apache Ambari: A web-based tool for provisioning, managing, and monitoring 
#     Apache Hadoop clusters
#   - This script prepares the base images with necessary dependencies for both
#     Bigtop and Ambari integration
#
# Usage:
#   ./update_bigtop_image.sh <distro> [image_name] [timezone]
#
# Parameters:
#   <distro>     - Linux distribution code
#                  Values: rocky8, rocky9, ubuntu22, ubuntu24
#   [image_name] - Optional custom base image name
#                  Format: REPOSITORY:TAG
#                  If not specified, default mapping will be used
#   [timezone]   - Optional timezone for the base image
#                  Format: Continent/City
#                  If not specified, default timezone will be used
#
# Default Image Mapping:
#   - rocky8  -> bigtop/puppet:trunk-rockylinux-8
#   - rocky9  -> bigtop/puppet:trunk-rockylinux-9
#   - ubuntu22 -> bigtop/puppet:trunk-ubuntu-22.04
#   - ubuntu24 -> bigtop/puppet:trunk-ubuntu-24.04
#
# Examples:
#   1. Update Rocky Linux 8 with default image:
#      ./update_bigtop_image.sh rocky8
#
#   2. Update Ubuntu 22.04 with custom image:
#      ./update_bigtop_image.sh ubuntu22 custom/ubuntu:22.04
#
# Dependencies Installed:
#   1. Development Tools:
#      - Python 3 development environment
#      - Java 8 and Java 17 JDK (required for Hadoop ecosystem)
#      - Rust and Cargo (for building native components)
#
#   2. System Tools:
#      - SSH client and server (for cluster communication)
#      - Network tools (curl, wget)
#      - Compression tools (tar, unzip)
#
#   3. Libraries:
#      - OpenSSL development libraries
#      - Cyrus SASL libraries (for secure authentication)
#      - Python packages (ansible, docker, jinja2)
#
# Important Notes:
#   1. Ensure Docker daemon is running
#   2. Sufficient disk space is required for new images
#   3. Docker operation permissions are needed
#   4. Backup important data before updating
#   5. When using custom images, ensure compatibility with target distribution
#
# Return Values:
#   0 - Success
#   1 - Parameter error or execution failure
#
###########################################

# Default configurations
DEFAULT_TIMEZONE="Asia/Shanghai"

# Enable strict mode
set -euo pipefail

# Display usage information
show_usage() {
    echo "Usage: $0 <distro> [image_name] [timezone]"
    echo "Supported distributions: rocky8, rocky9, ubuntu22, ubuntu24"
    echo "Examples:"
    echo "  Default image and timezone: $0 rocky8"
    echo "  Custom image: $0 rocky8 custom/rocky:8"
    echo "  Custom timezone: $0 rocky8 default Europe/London"
    echo "  Custom image and timezone: $0 rocky8 custom/rocky:8 Europe/London"
    exit 1
}

# Validate parameters
if [ $# -lt 1 ] || [ $# -gt 3 ]; then
    show_usage
fi

# Get parameters
DISTRO=$1
CUSTOM_IMAGE=${2:-""}
TIMEZONE=${3:-$DEFAULT_TIMEZONE}

# Validate timezone
if [ ! -f "/usr/share/zoneinfo/$TIMEZONE" ]; then
    echo "Error: Invalid timezone '$TIMEZONE'"
    echo "Please specify a valid timezone from /usr/share/zoneinfo/"
    exit 1
fi

# Default base image name mapping
declare -A DEFAULT_IMAGE_NAMES=(
    ["rocky8"]="bigtop/puppet:trunk-rockylinux-8"
    ["rocky9"]="bigtop/puppet:trunk-rockylinux-9"
    ["ubuntu22"]="bigtop/puppet:trunk-ubuntu-22.04"
    ["ubuntu24"]="bigtop/puppet:trunk-ubuntu-24.04"
)

# Validate distribution parameter
if [[ ! "${DEFAULT_IMAGE_NAMES[$DISTRO]+isset}" ]]; then
    echo "Error: Unsupported distribution '$DISTRO'"
    show_usage
fi

# Determine image name to use
if [ -n "$CUSTOM_IMAGE" ]; then
    IMAGE_NAME="$CUSTOM_IMAGE"
    echo "Using custom image: $IMAGE_NAME"
else
    IMAGE_NAME="${DEFAULT_IMAGE_NAMES[$DISTRO]}"
    echo "Using default image: $IMAGE_NAME"
fi

# Check if image exists
if ! docker images "$IMAGE_NAME" | grep -q "${IMAGE_NAME#*:}"; then
    echo "Error: Image $IMAGE_NAME not found"
    echo "Please pull the image first: docker pull $IMAGE_NAME"
    exit 1
fi

# Start new container
echo "Starting base container..."
CONTAINER_ID=$(docker run -d --privileged "$IMAGE_NAME" sleep infinity)

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: Failed to start container"
    exit 1
fi

echo "Container started, ID: $CONTAINER_ID"

# Cleanup function
cleanup() {
    echo "Cleaning up resources..."
    docker stop "$CONTAINER_ID" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_ID" >/dev/null 2>&1 || true
}

# Set cleanup on exit
trap cleanup EXIT

# Install dependencies for Rocky Linux
install_rocky_deps() {
    local version=$1
    echo "Installing dependencies for Rocky Linux $version..."
    
    # Enable devel repository for Rocky Linux
    echo "Enabling devel repository for Rocky Linux $version..."
    docker exec $CONTAINER_ID yum install -y yum-utils
    docker exec $CONTAINER_ID yum-config-manager --enable devel
    
    # Update package index
    docker exec $CONTAINER_ID yum clean all
    docker exec $CONTAINER_ID yum makecache

    # Install base packages
    docker exec $CONTAINER_ID yum -y install \
        sshpass python3-devel createrepo openssh-clients openssh-server httpd \
        rust cargo openssl-devel libffi-devel

    # Install development tools and runtime dependencies
    docker exec $CONTAINER_ID yum install -y \
        openssh-clients  unzip tar wget openssl chrony libtirpc-devel \
        python3-libselinux psmisc java-1.8.0-openjdk-devel java-17-openjdk-devel \
        python3-devel python3-libs python3-distro which \
        cyrus-sasl-devel cyrus-sasl-gssapi cyrus-sasl-plain

    # Install Python packages
    docker exec $CONTAINER_ID pip3 install pyyaml docker jinja2 setuptools-rust
    docker exec $CONTAINER_ID pip3 install ansible
    docker exec $CONTAINER_ID ansible-galaxy collection install ansible.posix -f
}

# Install dependencies for Ubuntu
install_ubuntu_deps() {
    local version=$1
    echo "Installing dependencies for Ubuntu $version..."

    # Update package index
    docker exec $CONTAINER_ID apt-get update

    # Set non-interactive frontend and timezone
    docker exec $CONTAINER_ID bash -c "export DEBIAN_FRONTEND=noninteractive && \
        ln -fs /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
        apt-get install -y tzdata"

    # Install base packages (with non-interactive mode)
    docker exec $CONTAINER_ID bash -c 'export DEBIAN_FRONTEND=noninteractive && \
        apt-get install -y \
        python3-pip python3-dev python-is-python3 \
        sshpass openssh-client openssh-server apache2 \
        rust-all cargo libssl-dev libffi-dev'

    # Install development tools and runtime dependencies (with non-interactive mode)
    docker exec $CONTAINER_ID bash -c 'export DEBIAN_FRONTEND=noninteractive && \
        apt-get install -y \
        curl unzip tar wget openssl chrony libtirpc-dev python3-selinux \
        psmisc openjdk-8-jdk openjdk-17-jdk python3-dev python3 python3-distro \
        libsasl2-dev libsasl2-modules-gssapi-mit libsasl2-modules'

    # Upgrade pip to latest version
    docker exec $CONTAINER_ID pip3 install --upgrade pip

    # Install Python packages
    docker exec $CONTAINER_ID pip3 install pyyaml docker jinja2 setuptools-rust
    docker exec $CONTAINER_ID pip3 install ansible
    docker exec $CONTAINER_ID ansible-galaxy collection install ansible.posix -f
}

# Install dependencies based on distribution
echo "Starting image update: $IMAGE_NAME"
case $DISTRO in
    rocky8|rocky9)
        install_rocky_deps "${DISTRO#rocky}"
        ;;
    ubuntu22|ubuntu24)
        install_ubuntu_deps "${DISTRO#ubuntu}"
        ;;
esac

# Commit changes to new image
echo "Committing changes to new image..."
docker commit $CONTAINER_ID $IMAGE_NAME

# Verify new image
echo "New image created successfully:"
docker images | grep $IMAGE_NAME

echo "Image update completed!"