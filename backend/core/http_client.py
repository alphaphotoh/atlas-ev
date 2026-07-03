import httpx


class HttpClient:

    TIMEOUT = httpx.Timeout(
        connect=20.0,
        read=30.0,
        write=20.0,
        pool=20.0
    )

    client = httpx.AsyncClient(
        timeout=TIMEOUT,
        http2=False
    )

    @staticmethod
    async def get(url: str, **kwargs):

        response = await HttpClient.client.get(
            url,
            **kwargs
        )

        response.raise_for_status()

        return response

    @staticmethod
    async def post(url: str, **kwargs):

        response = await HttpClient.client.post(
            url,
            **kwargs
        )

        response.raise_for_status()

        return response