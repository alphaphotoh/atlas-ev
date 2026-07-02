import asyncio


class AsyncUtils:

    @staticmethod
    async def gather(tasks):

        return await asyncio.gather(*tasks)