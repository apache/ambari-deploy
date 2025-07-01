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
Base Validator Module

This module defines the base Validator class that provides common functionality
for validating configuration data. It serves as a foundation for specific
validation implementations.
"""

class Validator:
    """
    Base Validator class for configuration validation.
    
    This abstract class defines the interface for all validator implementations
    and provides common functionality for collecting validation error messages.
    
    Attributes:
        err_messages (list): List to store validation error messages
    """
    
    def __init__(self):
        """
        Initialize the validator.
        
        Sets up an empty list to collect validation error messages.
        """
        self.err_messages = []

    def validate(self):
        """
        Abstract method to perform validation.
        
        This method must be implemented by subclasses to provide specific
        validation functionality.
        
        Returns:
            self: Returns the validator instance for method chaining
        """
        pass
