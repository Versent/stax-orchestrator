from unittest.mock import Mock, patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def get_stax_client_mock() -> Mock:
    """
    Patch get_stax_client for the duration of the test session
    """
    with patch("src.stax_orchestrator.get_stax_client") as stax_client_mock:
        yield stax_client_mock
