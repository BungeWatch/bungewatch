"""
Contains enums used throughout the application.
"""
import enum

class Sector(str, enum.Enum):
    """
    Enum representing different sectors.
    """
    AGRICULTURE = "agriculture"
    HEALTH = "health"
    EDUCATION = "education"
    FINANCE = "finance"
    LABOUR = "labour"
    ENVIRONMENT = "environment"
    TECHNOLOGY = "technology"
    LAND = "land"
    SECURITY = "security"
    GOVERNANCE = "governance"
    TRADE = "trade"
    INFRASTRUCTURE = "infrastructure"