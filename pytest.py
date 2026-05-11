import types

def fixture(func=None, **kwargs):
    if func is None:
        return lambda f: f
    return func

def mark_asyncio(func):
    return func

class Mark:
    async def __call__(self, func):
        return func

mark = types.SimpleNamespace(asyncio=Mark())
