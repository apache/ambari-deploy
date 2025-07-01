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

import json
from enum import Enum

import yaml


class FileManager:
    class FileType(Enum):
        RAW = "raw"
        JSON = "json"
        YAML = "yaml"

    @staticmethod
    def read_file(file_path, file_type: FileType):
        if file_type == FileManager.FileType.RAW:
            with open(file_path, "r") as file:
                return file.read()
        elif file_type == FileManager.FileType.JSON:
            with open(file_path, "r") as file:
                try:
                    return json.load(file)
                except Exception:
                    print("")
        elif file_type == FileManager.FileType.YAML:
            with open(file_path, "r") as file:
                return yaml.safe_load(file)
        else:
            raise ValueError("Unsupported file type")

    @staticmethod
    def write_file(file_path, data, file_type: FileType):
        if file_type == FileManager.FileType.RAW:
            with open(file_path, "w") as file:
                file.write(data)
        elif file_type == FileManager.FileType.JSON:
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
        elif file_type == FileManager.FileType.YAML:
            with open(file_path, "w") as file:
                yaml.dump(data, file)
        else:
            raise ValueError("Unsupported file type")
