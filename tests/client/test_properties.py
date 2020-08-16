from httpx import URL, AsyncClient, Cookies, Headers, Timeout


def test_client_base_url():
    client = AsyncClient()
    client.base_url = "https://www.example.org/"  # type: ignore
    assert isinstance(client.base_url, URL)
    assert client.base_url == URL("https://www.example.org/")


def test_client_base_url_without_trailing_slash():
    client = AsyncClient()
    client.base_url = "https://www.example.org/path"  # type: ignore
    assert isinstance(client.base_url, URL)
    assert client.base_url == URL("https://www.example.org/path/")


def test_client_base_url_with_trailing_slash():
    client = AsyncClient()
    client.base_url = "https://www.example.org/path/"  # type: ignore
    assert isinstance(client.base_url, URL)
    assert client.base_url == URL("https://www.example.org/path/")


def test_client_headers():
    client = AsyncClient()
    client.headers = {"a": "b"}  # type: ignore
    assert isinstance(client.headers, Headers)
    assert client.headers["A"] == "b"


def test_client_cookies():
    client = AsyncClient()
    client.cookies = {"a": "b"}  # type: ignore
    assert isinstance(client.cookies, Cookies)
    mycookies = list(client.cookies.jar)
    assert len(mycookies) == 1
    assert mycookies[0].name == "a" and mycookies[0].value == "b"


def test_client_timeout():
    expected_timeout = 12.0
    client = AsyncClient()

    client.timeout = expected_timeout  # type: ignore

    assert isinstance(client.timeout, Timeout)
    assert client.timeout.connect == expected_timeout
    assert client.timeout.read == expected_timeout
    assert client.timeout.write == expected_timeout
    assert client.timeout.pool == expected_timeout
