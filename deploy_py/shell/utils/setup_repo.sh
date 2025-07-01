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

# Check required parameters
if [ "$#" -lt 3 ]; then
    log_error "Insufficient parameters"
    log "Usage: $0 <repo_path> <create_http_repo> <http_port> [os_type]"
    log "  repo_path: Local repository path"
    log "  create_http_repo: true/false whether to create HTTP repository"
    log "  http_port: Port number for HTTP repository service"
    log "  os_type: Operating system type (optional, auto-detected by default)"
    exit 1
fi

REPO_PATH="$1"
CREATE_HTTP_REPO="$2"
HTTP_PORT="$3"

log_debug "Input parameters: REPO_PATH=$REPO_PATH, CREATE_HTTP_REPO=$CREATE_HTTP_REPO, HTTP_PORT=$HTTP_PORT"

# Auto-detect OS_TYPE if not provided
if [ "$#" -ge 4 ]; then
    OS_TYPE="$4"
    log_debug "Using specified OS type: $OS_TYPE"
else
    log_debug "Starting automatic OS detection..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_debug "ID read from /etc/os-release: $ID"
        OS_TYPE=$(echo "$ID" | tr '[:upper:]' '[:lower:]')
        log_debug "OS_TYPE after lowercase conversion: $OS_TYPE"
        
        if [[ "$OS_TYPE" == "ubuntu"* ]]; then
            OS_TYPE="ubuntu"
            log_debug "Detected Ubuntu system"
        elif [[ "$OS_TYPE" == "rocky"* ]]; then
            OS_TYPE="rocky"
            log_debug "Detected Rocky Linux system"
        elif [[ "$OS_TYPE" == "centos"* || "$OS_TYPE" == "rhel"* ]]; then
            OS_TYPE="redhat"
            log_debug "Detected CentOS/RHEL system"
        fi
    else
        log_error "Cannot find /etc/os-release file"
        exit 1
    fi
fi

log "Setting up repository: path=$REPO_PATH, Create HTTP repository=$CREATE_HTTP_REPO, HTTP port=$HTTP_PORT, System type=$OS_TYPE"

# Check if repository path exists
if [ ! -d "$REPO_PATH" ]; then
    log_error "Repository path $REPO_PATH does not exist"
    exit 1
fi
log_debug "Repository path existence check passed"

# Check if OS type is supported
if [[ "$OS_TYPE" != "ubuntu" && "$OS_TYPE" != "rocky" && "$OS_TYPE" != "redhat" ]]; then
    log_error "Unsupported operating system type $OS_TYPE"
    exit 1
fi
log_debug "Operating system type check passed"

# Function to set up YUM repository for RHEL-based systems
setup_yum_repo() {
    local repo_path="$1"
    log "Starting YUM repository setup..."
    
    # Remove existing repodata directory
    if [ -d "${repo_path}/repodata" ]; then
        log_debug "Removing existing repodata directory"
        rm -rf "${repo_path}/repodata"
    fi
    
    # Create new YUM repository
    log_debug "Starting creation of new YUM repository"
    createrepo -o "$repo_path" "$repo_path"
    if [ $? -ne 0 ]; then
        log_error "Failed to create YUM repository"
        return 1
    fi
    log_debug "YUM repository created successfully"

    # Configure and start httpd if HTTP repository is requested
    if [ "$CREATE_HTTP_REPO" = "true" ]; then
        log "Configuring HTTP service..."
        # Install httpd if not installed
        if ! command -v httpd &> /dev/null; then
            log_debug "httpd not installed, installing now"
            yum install -y httpd
            log_debug "httpd installation completed"
        fi
        
        # Configure httpd with specified port
        cat > /etc/httpd/conf/httpd.conf << EOF
ServerRoot "/etc/httpd"
Listen ${HTTP_PORT}
Include conf.modules.d/*.conf
User apache
Group apache
ServerAdmin root@localhost
DocumentRoot "${repo_path}"
<Directory />
    AllowOverride none
    Require all granted
</Directory>
<Directory "${repo_path}">
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
    allow from all
    IndexOptions FancyIndexing FoldersFirst NameWidth=* DescriptionWidth=* SuppressHTMLPreamble HTMLTable
    IndexOptions Charset=utf-8 IconHeight=16 IconWidth=16 SuppressRules
</Directory>
EnableSendfile on
IncludeOptional conf.d/*.conf
EOF
        
        # Stop any running httpd processes
        pkill -f httpd || true
        
        # Start httpd service
        if [ "$OS_TYPE" == "rocky" ]; then
            systemctl start httpd
        else
            service httpd start
        fi
        
        # Check service status
        if systemctl is-active --quiet httpd; then
            log "httpd service started successfully on port ${HTTP_PORT}"
        else
            log_error "Failed to start httpd service"
        fi
    fi
}

# Function to set up APT repository for Debian-based systems
setup_apt_repo() {
    local repo_path="$1"
    local distribution="jammy"
    log "Starting APT repository setup..."
    
    # Clean old repository files
    log_debug "Cleaning old repository files..."
    rm -rf "${repo_path}/dists"
    
    # Create repository directory structure
    log_debug "Creating repository directory structure..."
    mkdir -p "${repo_path}/dists/${distribution}/main/binary-amd64"
    
    # Generate Packages file
    log_debug "Generating Packages file..."
    cd "${repo_path}"
    dpkg-scanpackages . /dev/null > "dists/${distribution}/main/binary-amd64/Packages"
    gzip -k -f "dists/${distribution}/main/binary-amd64/Packages"

    # Generate Release file
    log_debug "Generating Release file..."
    cd "${repo_path}/dists/${distribution}"
    apt-ftparchive release . > Release

    # Configure Apache2 if HTTP repository is requested
    if [ "$CREATE_HTTP_REPO" = "true" ]; then
        log_debug "Configuring Apache2..."
        apt-get install -y apache2
        cat > /etc/apache2/sites-available/000-default.conf << EOF
<VirtualHost *:${HTTP_PORT}>
    DocumentRoot ${repo_path}
    <Directory ${repo_path}>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
EOF
        sed -i "s/Listen 80/Listen ${HTTP_PORT}/" /etc/apache2/ports.conf
        systemctl restart apache2
        log "Apache2 service started successfully on port ${HTTP_PORT}"
    fi

    log "APT repository setup completed"
}

# Set up repository based on OS type
log "Selecting repository setup method based on OS type..."
if [ "$OS_TYPE" == "ubuntu" ]; then
    setup_apt_repo "$REPO_PATH"
else
    setup_yum_repo "$REPO_PATH"
fi

log "Repository setup completed" 