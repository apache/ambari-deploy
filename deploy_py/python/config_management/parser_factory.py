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
Parser Factory Module

This module implements a factory pattern for creating parser instances.
It provides functionality to register and retrieve different types of parsers
through a centralized factory class.
"""

def to_camel_case(name):
    """
    Convert a string from snake_case to camelCase.
    
    Args:
        name (str): The string to be converted.
        
    Returns:
        str: The converted string in camelCase format.
        
    Raises:
        ValueError: If the input name is not a string.
        
    Example:
        >>> to_camel_case("hello_world")
        "helloWorld"
    """
    if not isinstance(name, str):
        raise ValueError("Input 'name' must be a string")

    if not name:
        return ""

    if "_" not in name:
        return name

    return "".join(word.capitalize() for word in name.split("_"))


class ParserFactory:
    """
    Factory class for creating and managing parser instances.
    
    This class implements the Factory pattern to manage different types of parsers.
    It maintains a registry of parser classes and provides methods to register
    new parsers and retrieve parser instances by type.
    
    Class Attributes:
        _parsers (dict): Registry mapping parser names to parser classes
    """
    
    _parsers = {}

    @classmethod
    def register_parser(cls, parser_cls):
        """
        Register a new parser class with the factory.
        
        The parser name is derived from the class name converted to camelCase.
        
        Args:
            parser_cls: The parser class to register
        """
        parser_name = to_camel_case(parser_cls.__name__).lower()
        cls._parsers[parser_name] = parser_cls

    @classmethod
    def get_parser(cls, parser_type):
        """
        Get a parser instance by type.
        
        Args:
            parser_type (str): The type of parser to retrieve
            
        Returns:
            Parser: A new instance of the requested parser
            
        Raises:
            ValueError: If the requested parser type is not registered
        """
        parser_class = cls._parsers.get(parser_type)
        if not parser_class:
            raise ValueError(f"Unknown parser type: {parser_type}")
        return parser_class()
