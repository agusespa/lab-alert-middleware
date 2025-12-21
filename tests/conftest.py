import os

os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/test/test"

import pytest

@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Ensure test environment variables are set"""
    pass
