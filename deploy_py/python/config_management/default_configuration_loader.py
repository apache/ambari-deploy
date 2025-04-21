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

import os

from python.config_management.file_manager import *


class DefaultConfigurationLoader:
    def __init__(self, conf_dir, format=FileManager.FileType.YAML):
        self.format = format
        self.conf_dir = conf_dir

    def load_conf(self, conf_name):
        file_path = os.path.join(self.conf_dir, conf_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        content = FileManager.read_file(file_path, self.format)
        return content
