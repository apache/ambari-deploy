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


# Logging functions for different message levels
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_debug() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [DEBUG] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >&2
}

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running in Docker environment and set default root password
IS_DOCKER=${1:-false}
ROOT_PASSWORD=${2:-"B767610qa4Z"}  # Default root password if not provided

log "Starting Ubuntu environment setup..."

# Set systemctl configuration
SYSTEMCTL_FILE="systemctl3.py"
PYTHON_VERSION="python3"

# Function to setup systemctl script
setup_systemctl() {
    log_debug "Setting up systemctl script..."
    local systemctl_file="$SCRIPT_DIR/$SYSTEMCTL_FILE"
    if [ -f "$systemctl_file" ]; then
        log_debug "Found systemctl script: $systemctl_file"
        \cp "$systemctl_file" /usr/bin/systemctl
        chmod +x /usr/bin/systemctl
        log_debug "Systemctl script installed successfully"
        return 0
    else
        log_error "Systemctl script not found: $systemctl_file"
        return 1
    fi
}

# Set non-interactive frontend to prevent prompts during package installation
export DEBIAN_FRONTEND=noninteractive

# Create necessary directories and files for system configuration
log_debug "Creating necessary directories and files"
mkdir -p /etc/default
touch /etc/default/rng-tools

# Update package list to ensure we have the latest information
log_debug "Updating package list"
apt-get update

# Install basic utilities needed for system configuration
log_debug "Installing basic utilities"
apt-get install -y apt-utils dialog 2>&1
apt-get install -y locales rng-tools-debian systemd udev 2>&1

# Install required packages for development and system management
log_debug "Installing required packages"
apt-get install -y \
    python3-dev \
    dpkg-dev \
    reprepro \
    openssh-client \
    openssh-server \
    apache2 \
    curl \
    sshpass \
    python3-pip \
    rust-all \
    libssl-dev \
    python-is-python3 \
    libffi-dev \
    2>&1

# Create Python symlink if not exists
log_debug "Setting up Python symlink"
if ! command -v python &> /dev/null; then
    ln -sf /usr/bin/python3 /usr/bin/python
fi

# Configure system locale to UTF-8
log_debug "Setting up locale"
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8

# Function to configure SSH server and client
configure_ssh() {
    log_debug "Starting SSH configuration..."
    
    # Generate SSH host keys for secure communication
    log_debug "Generating SSH host keys"
    if ! ssh-keygen -A; then
        log_error "Failed to generate SSH host keys"
        return 1
    fi
    
    # Copy SSH configuration from template
    log_debug "Copying SSH configuration file"
    if [ -f "$SCRIPT_DIR/sshd_config_template" ]; then
        cp "$SCRIPT_DIR/sshd_config_template" /etc/ssh/sshd_config
        chmod 600 /etc/ssh/sshd_config
        log_debug "SSH configuration file updated"
    else
        log_error "SSH config template not found: $SCRIPT_DIR/sshd_config_template"
        return 1
    fi
    

    
    # Restart SSH service (skip in Docker environment)
    if [ "$IS_DOCKER" = "true" ]; then
        log_debug "Skipping SSH service restart in Docker environment"
        # Set root password for SSH access
        log_debug "Setting root password"
        if ! echo "root:$ROOT_PASSWORD" | chpasswd; then
            log_error "Failed to set root password"
            return 1
        fi
    else
        log_debug "Restarting SSH service"
        if ! systemctl restart ssh.service; then
            log_error "Failed to restart SSH service"
            return 1
        fi
        log_debug "SSH service restarted successfully"
    fi
    
    log_debug "SSH configuration completed"
    return 0
}

# Special handling for Docker environment
if [ "$IS_DOCKER" = "true" ]; then
    log_debug "Applying Docker-specific configurations"
    
    # Setup systemctl script for Docker environment
    setup_systemctl
    
    # Create policy to prevent automatic service startup
    cat > /usr/sbin/policy-rc.d << 'EOF'
#!/bin/sh
exit 101
EOF
    chmod +x /usr/sbin/policy-rc.d
    
    # Configure random number generator for Docker
    cat > /etc/default/rng-tools << EOF
HRNGDEVICE=/dev/urandom
RNGD_OPTS="-r /dev/urandom"
EOF
fi

# Configure SSH server
configure_ssh

# Install Python dependencies required for deployment
log_debug "Installing Python dependencies"
pip3 install --no-cache-dir \
    pyyaml \
    docker \
    jinja2 \
    setuptools-rust

# Install Ansible and its collections
log_debug "Installing Ansible"
if pip3 install --no-cache-dir ansible; then
    log_debug "Ansible installation successful"
    
    # Install required Ansible collections
    log_debug "Installing Ansible collections"
    ansible-galaxy collection install ansible.posix -f
else
    log_error "Ansible installation failed"
    exit 1
fi

# Ensure SSH service is running
service ssh restart

log "Ubuntu environment setup completed"
exit 0

