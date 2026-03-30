# -*- encoding: utf-8 -*-
"""
速率限制器配置
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
