import asyncio


class AsyncUtils:

    MAX_CONCURRENT = 3

    @staticmethod
    async def gather(tasks):

        semaphore = asyncio.Semaphore(

            AsyncUtils.MAX_CONCURRENT

        )

        async def run(task):

            async with semaphore:

                return await task

        return await asyncio.gather(

            *(

                run(task)

                for task in tasks

            )

        )