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

# !/usr/bin/python3
# -*- coding: UTF-8 -*-
import logging
from logging.handlers import MemoryHandler

from .constants import *


def get_logger(
    name="bigdata_deploy_logger", log_file="bigdata_deploy.log", level=logging.DEBUG
):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(f"{LOGS_DIR}/{log_file}")
        file_handler.setLevel(level)

        memory_handler = MemoryHandler(capacity=20, target=file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        memory_handler.setFormatter(formatter)

        logger.addHandler(memory_handler)
        logger.addHandler(console_handler)
    return logger
