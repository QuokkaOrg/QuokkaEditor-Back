import asyncio

import httpx


async def test_sync():
    async with httpx.AsyncClient() as client:
        await client.post(
            url="http://localhost:8100/documents/8fa4e12a-5bce-47c5-87c2-f3211dbd9f19/sync/",
            json=[
                {"pos": 0, "char": "h", "type": "INSERT"},
                {"pos": 1, "char": "e", "type": "INSERT"},
                {"pos": 2, "char": "j", "type": "INSERT"},
            ],
        )


async def test_sync2():
    async with httpx.AsyncClient() as client:
        await asyncio.sleep(0.001)
        await client.post(
            url="http://localhost:8100/documents/8fa4e12a-5bce-47c5-87c2-f3211dbd9f19/sync/",
            json=[
                {"pos": 0, "char": "n", "type": "INSERT"},
                {"pos": 1, "char": "i", "type": "INSERT"},
                {"pos": 2, "char": "e", "type": "INSERT"},
            ],
        )


async def main():
    await asyncio.gather(*[test_sync2(), test_sync()])


if __name__ == "__main__":
    asyncio.run(main())
