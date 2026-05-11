import pytest
import asyncio

@pytest.mark.asyncio
async def test_dummy():
    await asyncio.sleep(0)
    assert True
