import logging
import asyncio
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from .models import UserContainer, RouteMetrics
from .route_manager import K8sRouteManager
from .health_checker import HealthChecker
from .registry import ContainerRegistry