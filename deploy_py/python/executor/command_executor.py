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

# -*- coding:utf8 -*-
# !/usr/bin/python3

"""
Command Executor Module

This module provides a utility class for executing shell commands with
proper logging and error handling. It supports both direct command execution
and execution with log file output.
"""

import subprocess

from python.common.basic_logger import get_logger
from python.common.constants import *

logger = get_logger()


class CommandExecutor:
    """
    Utility class for executing shell commands.
    
    This class provides static methods to execute shell commands with:
    - Proper logging of command execution
    - Error handling and status reporting
    - Support for working directory specification
    - Environment variable configuration
    - Output redirection to log files
    """
    
    @staticmethod
    def execute_command(
        command, workdir=None, env_vars=None, shell=False, logfile=None
    ):
        """
        Execute a shell command with configurable options.
        
        Args:
            command: Command to execute (string or list)
            workdir: Working directory for command execution
            env_vars: Environment variables for the command
            shell: Whether to run command through shell
            logfile: File object to write command output
            
        Returns:
            If logfile is provided:
                int: Exit status of the command
            Otherwise:
                tuple: (exit_code, stdout, stderr)
                
        Note:
            When logfile is provided, both stdout and stderr are written to it
        """
        out = logfile or subprocess.PIPE
        print(f"Executing  command: {command}")
        env_vars = dict(env_vars) if env_vars else env_vars
        try:
            process = subprocess.Popen(
                command,
                stdout=out,
                stderr=out,
                shell=shell,
                cwd=workdir,
                env=env_vars,
                universal_newlines=True,
            )

            if logfile:
                exit_status = process.wait()
                return exit_status

            output, error = process.communicate()
            exit_code = process.returncode
            if exit_code == 0:
                logger.info(f"Command executed successfully: {command}")
            else:
                logger.error(
                    f"Command failed with exit code {exit_code}: cmd: {command}, out: {output}, err:{error}"
                )
            return exit_code, output, error
        except Exception as e:
            logger.error(f"Exception occurred while executing command: {e}")
            return -1, "", str(e)

    @staticmethod
    def execute_command_withlog(
        command, log_file, workdir=None, env_vars=None, shell=False
    ):
        """
        Execute a command and write output to a log file.
        
        This method is a wrapper around execute_command that automatically
        handles log file management.
        
        Args:
            command: Command to execute (string or list)
            log_file: Path to the log file
            workdir: Working directory for command execution
            env_vars: Environment variables for the command
            shell: Whether to run command through shell
            
        Returns:
            int: Exit status of the command
        """
        with open(log_file, "a") as log:
            exit_status = CommandExecutor.execute_command(
                command, workdir, env_vars, shell, logfile=log
            )
            return exit_status
