"""
Configuration module for OpenAI API key management.

This module loads and validates the OPENAI_API_KEY from the environment
using the .env file. It provides centralized configuration management
and ensures the API key is properly configured before use.
"""

import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


def _validate_api_key() -> str:
    """
    Validate and retrieve the OpenAI API key from environment.
    
    Returns:
        str: The validated OpenAI API key
        
    Raises:
        ValueError: If OPENAI_API_KEY is missing or empty
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key is None or api_key.strip() == "":
        raise ValueError(
            "OPENAI_API_KEY not found in environment. "
            "Please check your .env file and ensure OPENAI_API_KEY is properly configured. "
            "Refer to .env.example for the expected format."
        )
    
    return api_key


# Validate and load the API key at module import time
OPENAI_API_KEY = _validate_api_key()
