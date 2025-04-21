"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from python.common.constants import *
from .base_configuration import *
import os

class AdvancedConfiguration(BaseConfiguration):
    def __init__(self, name=CONF_NAME):
        super().__init__(name)

    def is_ambari_repo_configured(self):
        repos = self.get("repos", [])
        if not repos:
            return False
        if len(repos) > 0:
            for repo_item in repos:
                if "ambari_repo" == repo_item["name"]:
                    return True
        return False

    def has_any_ambari_repo(self):
        """Check if either HTTP or file repository is configured"""
        repos = self.get("repos", [])
        if not repos:
            return False
        for repo_item in repos:
            if repo_item["name"] == "ambari_repo":
                return True
        return False

    def has_repo_pkgs(self):
        """Check if any repository packages are configured"""
        repo_pkgs_dir = self.get("repo_pkgs_dir", "")
        if not repo_pkgs_dir:
            return False
        if not os.path.exists(repo_pkgs_dir):
            return False
        return True