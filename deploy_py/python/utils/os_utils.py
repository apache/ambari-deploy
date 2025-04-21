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
import platform
import shutil

try:
    import distro
    HAS_DISTRO = True
except ImportError:
    HAS_DISTRO = False

import subprocess
import sys
import time
from contextlib import contextmanager

from jinja2 import Template

from python.common.basic_logger import get_logger

logger = get_logger()


def get_os_arch():
    return platform.machine()


def get_os_type():
    operatingSystem = platform.system().lower()
    if operatingSystem == "linux":
        try:
            if HAS_DISTRO:
                operatingSystem = distro.id().lower()
            else:
                operatingSystem = platform.linux_distribution()[0].lower()
        except Exception as e:
            logger.warning(f"Failed to get Linux distribution: {e}")
            # If all else fails, try to get information from /etc/os-release file
            try:
                with open('/etc/os-release') as f:
                    for line in f:
                        if line.startswith('ID='):
                            operatingSystem = line.split('=')[1].strip().strip('"').lower()
                            break
            except Exception as e:
                logger.error(f"Failed to read /etc/os-release: {e}")

    # special cases
    if operatingSystem.startswith("ubuntu"):
        operatingSystem = "ubuntu"
    elif operatingSystem.startswith("red hat enterprise linux"):
        operatingSystem = "redhat"
    elif operatingSystem.startswith("kylin linux"):
        operatingSystem = "kylin"
    elif operatingSystem.startswith("centos linux"):
        operatingSystem = "redhat"
    elif operatingSystem.startswith("rocky linux"):
        operatingSystem = "rocky"
    elif operatingSystem.startswith("uos"):
        operatingSystem = "uos"
    elif operatingSystem.startswith("anolis"):
        operatingSystem = "anolis"
    elif operatingSystem.startswith("asianux server"):
        operatingSystem = "asianux"
    elif operatingSystem.startswith("bclinux"):
        operatingSystem = "bclinux"
    elif operatingSystem.startswith("openeuler"):
        operatingSystem = "openeuler"

    if operatingSystem == "":
        raise Exception("Cannot detect os type. Exiting...")

    return operatingSystem


def get_os_version():
    os_type = get_os_type()
    try:
        if HAS_DISTRO:
            version = distro.version()
        else:
            version = platform.linux_distribution()[1]
    except Exception as e:
        logger.warning(f"Failed to get OS version: {e}")
        # If all else fails, try to get information from /etc/os-release file
        try:
            with open('/etc/os-release') as f:
                for line in f:
                    if line.startswith('VERSION_ID='):
                        version = line.split('=')[1].strip().strip('"')
                        break
        except Exception as e:
            logger.error(f"Failed to read /etc/os-release: {e}")
            raise Exception("Cannot detect os version. Exiting...")

    if version:
        if os_type == "kylin":
            # kylin v10
            if version == "V10":
                version = "v10"
        elif os_type == "anolis":
            if version == "20":
                version = "20"
        elif os_type == "uos":
            # uos 20
            if version == "20":
                version = "20"
        elif os_type == "openeuler":
            # openeuler 22
            version = "22"
        elif os_type == "bclinux":
            version = "8"
        elif os_type == "4.0.":
            # support nfs (zhong ke fang de)
            version = "4"
        elif len(version.split(".")) > 2:
            # support 8.4.0
            version = version.split(".")[0]
        else:
            version = version
        return version
    else:
        raise Exception("Cannot detect os version. Exiting...")


def get_full_os_major_version():
    os_type = get_os_type()
    os_version = get_os_version()
    os_arch = get_os_arch()
    full_os_major_version = f"{os_type}{os_version}_{os_arch}"
    logger.info(f"full_os_and_major_version is {full_os_major_version}")
    return full_os_major_version



def copy_file(src, dst):
    with open(src, "rb") as fsrc:
        with open(dst, "wb") as fdst:
            fdst.write(fsrc.read())


@contextmanager
def smart_open(file: str, mode: str, *args, **kwargs):
    if file == "-":
        if "w" in mode:
            yield sys.stdout.buffer
        else:
            yield sys.stdin.buffer
        return
    with open(file, mode, *args, **kwargs) as fh:
        yield fh



def render_template(template_path, context, output_path):
    """
    #  Renders content from a specified template file and writes it to an output file.
    # :param template_path: The path to the template file.
    # :param context: A dictionary containing variables to be used in rendering the template.
    # :param output_path: The file path where the rendered content will be written.
    """
    with open(template_path, "r") as template_file:
        template_content = template_file.read()

    template = Template(template_content)
    rendered_content = template.render(context)

    with open(output_path, "w") as output_file:
        output_file.write(rendered_content)


def get_ip_address():
    try:
        ip = (
            subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
            .decode()
            .strip()
        )
        return ip
    except subprocess.CalledProcessError as e:
        return "Unable to obtain IP address.: " + str(e)
