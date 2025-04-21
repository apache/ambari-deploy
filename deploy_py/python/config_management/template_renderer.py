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

import yaml
from jinja2 import Template

from python.common.basic_logger import get_logger

logger = get_logger()


class TemplateRenderer:
    def __init__(self):
        self.rendered_result = None

    def render_template(self, template_str, context):
        # template_str = FileManager.read_file(self.file_path)
        if not template_str:
            return {}
        template = Template(template_str)
        logger.debug(
            f"Rendering config templates, template_str: {template_str}, context:{context}"
        )
        self.rendered_result = template.render(context)
        return self

    def decode_result(self, decoder="json"):
        if not self.rendered_result:
            raise Exception("render_template first")
        if decoder == "json":
            return json.loads(self.rendered_result)
        elif decoder == "yaml":
            return yaml.safe_load(self.rendered_result)
        else:
            raise ValueError("Unsupported decoder specified")
