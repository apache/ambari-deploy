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
Validation Manager Module

This module provides a centralized manager for executing multiple validators
and collecting their validation results. It coordinates the validation process
across different validation components.
"""

class ValidationManager:
    """
    Manager class for coordinating multiple validators.
    
    This class manages a collection of validators and provides methods to
    execute all validators and collect their validation results.
    
    Attributes:
        validators (list): List of validator instances to be executed
    """
    
    def __init__(self, validators):
        """
        Initialize the validation manager.
        
        Args:
            validators (list): List of validator instances to manage
        """
        self.validators = validators

    def validate_all(self):
        """
        Execute all validators and collect their error messages.
        
        This method runs each validator in sequence and aggregates
        any error messages they produce.
        
        Returns:
            list: Combined list of error messages from all validators
        """
        errors = []
        for validator in self.validators:
            errors.extend(validator.validate().err_messages)
        return errors
