"""
Configuration settings for the Multi-Agent Research Assistant
This file loads environment variables and provides them to the application
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables"""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    
    # Model Settings
    OPENAI_MODEL: str = "gpt-4o-mini"  # Using the efficient mini model
    TEMPERATURE: float = 0.7  # Creativity level (0=deterministic, 1=creative)
    
    # Debug
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    def validate(self):
        """Check if all required API keys are present"""
        errors = []
        
        if not self.OPENAI_API_KEY:
            errors.append("❌ Missing OPENAI_API_KEY in .env file")
        
        if not self.TAVILY_API_KEY:
            errors.append("❌ Missing TAVILY_API_KEY in .env file")
        
        if errors:
            print("\n".join(errors))
            print("\n💡 Tip: Get Tavily API key free at https://tavily.com")
            return False
        
        print("✅ All API keys loaded successfully!")
        return True

# Create a single instance to use throughout the app
settings = Settings()