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


# The IP address of the master server
MASTER_SERVER="192.168.1.100"  # Please replace with the actual IP address of the master server

# The list of IP addresses of the slave servers
SLAVE_SERVERS=("192.168.1.101" "192.168.1.102" "192.168.1.103")  # Please replace with the actual IP addresses of the slave servers

# Check if the user is root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root"
  exit 1
fi

# Install and configure chrony on the master server
setup_master() {
  echo "Configuring master server $MASTER_SERVER..."

  # Install chrony
  dnf install -y chrony

  # Configure chrony as a time server
  cat > /etc/chrony.conf <<EOF
server 0.centos.pool.ntp.org iburst
server 1.centos.pool.ntp.org iburst
server 2.centos.pool.ntp.org iburst
server 3.centos.pool.ntp.org iburst

allow 0.0.0.0/0
local stratum 10
logdir /var/log/chrony
makestep 1 3
rtcsync
EOF

  # Start and enable the chronyd service
  systemctl enable --now chronyd
  systemctl restart chronyd

  # Check the status of the service
  systemctl status chronyd | grep "active (running)"
  if [ $? -eq 0 ]; then
    echo "Master server $MASTER_SERVER configured and running"
  else
    echo "Master server $MASTER_SERVER configuration failed"
    exit 1
  fi
}

# Install and configure chrony on the slave servers
setup_slaves() {
  for SLAVE in "${SLAVE_SERVERS[@]}"; do
    echo "Configuring slave server $SLAVE..."

    ssh root@$SLAVE "dnf install -y chrony"

    ssh root@$SLAVE "cat > /etc/chrony.conf" <<EOF
server $MASTER_SERVER iburst
logdir /var/log/chrony
EOF

    ssh root@$SLAVE "systemctl enable --now chronyd"
    ssh root@$SLAVE "systemctl restart chronyd"

    # Check the status of the service
    ssh root@$SLAVE "systemctl status chronyd | grep 'active (running)'"
    if [ $? -eq 0 ]; then
      echo "Slave server $SLAVE configured and running"
    else
      echo "Slave server $SLAVE configuration failed"
      exit 1
    fi
  done
}

# Main program
echo "Starting to configure time synchronization servers..."

# Configure the master server
setup_master

# Configure the slave servers
setup_slaves

echo "All servers time synchronization configuration completed!"
