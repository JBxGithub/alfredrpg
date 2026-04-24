"""
Test suite for Futu Trading Bot
富途交易機器人測試套件
"""

import pytest
from src.utils.logger import get_logger


def test_logger():
    """Test logger initialization"""
    logger = get_logger(__name__)
    assert logger is not None
    logger.info("Test log message")


def test_basic_assertion():
    """Basic test to verify test suite is working"""
    assert True
