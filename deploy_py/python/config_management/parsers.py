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

"""
Base Parser Module

This module defines the base Parser class that provides common functionality
for parsing configuration data. It includes support for expanding range patterns
in configuration strings.
"""

import re


class Parser:
    """
    Base Parser class for configuration parsing.
    
    This abstract class defines the interface for all parser implementations
    and provides common utility methods for parsing configuration data.
    """
    
    def parse(self, *args, **kwargs):
        """
        Abstract method to parse configuration data.
        
        This method must be implemented by subclasses to provide specific
        parsing functionality.
        
        Args:
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments
            
        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError("Parse method must be implemented by subclasses")

    def _expand_range(self, pattern):
        """
        Expand numeric range patterns in a string.
        
        Supports patterns like [1-3] which expands to a list of values
        with numbers 1 through 3 inclusive.
        
        Args:
            pattern (str): String containing range pattern (e.g., "node[1-3]")
            
        Returns:
            list: List of strings with expanded range values
                 (e.g., ["node1", "node2", "node3"])
        """
        match = re.search(r"\[(\d+)-(\d+)]", pattern)
        if match:
            prefix = pattern[: match.start()]
            start = int(match.group(1))
            end = int(match.group(2))
            suffix = pattern[match.end() :]
            return [f"{prefix}{i}{suffix}" for i in range(start, end + 1)]
        else:
            return [pattern]
