# Models package for InstantIn.me platform
# This file exposes all database models for the Link-in-Bio Commerce Platform

# User and authentication models
from .user import User

# Core business models  
# Note: Import statements will be uncommented as models are created in subsequent tasks

from .storefront import Storefront                    # Task 3.2
from .product import Product                          # Task 3.3  
from .order import Order                              # Task 3.4
from .order_item import OrderItem                     # Task 3.5
from .drop import Drop                                # Task 3.6
from .drop_participant import DropParticipant         # Task 3.7
from .raffle import Raffle, RaffleEntry               # Task 3.8
from .analytics import PageView                       # Task 3.9

# Collaborative features
# from .drop import Drop                                # Task 3.6
# from .drop_participant import DropParticipant         # Task 3.7

# Gamification and rewards
# from .raffle import Raffle, RaffleEntry               # Task 3.8

# Analytics and tracking
# from .analytics import PageView                       # Task 3.9

# Current available models
__all__ = [
    "User",
    "Storefront",     # Task 3.2
    "Product",        # Task 3.3 
    "Order",          # Task 3.4
    "OrderItem",      # Task 3.5
    "Drop",           # Task 3.6
    "DropParticipant", # Task 3.7
    "Raffle",         # Task 3.8
    "RaffleEntry",    # Task 3.8
    "PageView",       # Task 3.9
    # Add new models here as they are created:
]

# Model registry for SQLAlchemy metadata
# All models are automatically registered with Base.metadata when imported
# This ensures proper table creation and migration detection 