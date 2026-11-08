import httpx2


def scripted_client(responses: list[httpx2.Response], requests: list[httpx2.Request] | None = None,
                    base_url: str = "https://api.test") -> httpx2.Client:
    """Returns the responses in order, and records each request if a list is given."""
    remaining = list(responses)

    def handler(request: httpx2.Request) -> httpx2.Response:
        if requests is not None:
            requests.append(request)
        return remaining.pop(0)

    return httpx2.Client(base_url=base_url, transport=httpx2.MockTransport(handler))
