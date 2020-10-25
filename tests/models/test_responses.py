import json
from unittest import mock

import brotli
import pytest

import httpx


class StreamingBody:
    def __iter__(self):
        yield b"Hello, "
        yield b"world!"


def streaming_body():
    yield b"Hello, "
    yield b"world!"


async def async_streaming_body():
    yield b"Hello, "
    yield b"world!"


def test_response():
    response = httpx.Response(
        200,
        content=b"Hello, world!",
        request=httpx.Request("GET", "https://example.org"),
    )

    assert response.status_code == 200
    assert response.reason_phrase == "OK"
    assert response.text == "Hello, world!"
    assert response.request.method == "GET"
    assert response.request.url == "https://example.org"
    assert not response.is_error


def test_response_content():
    response = httpx.Response(200, content="Hello, world!")

    assert response.status_code == 200
    assert response.reason_phrase == "OK"
    assert response.text == "Hello, world!"
    assert response.headers == {"Content-Length": "13"}


def test_response_text():
    response = httpx.Response(200, text="Hello, world!")

    assert response.status_code == 200
    assert response.reason_phrase == "OK"
    assert response.text == "Hello, world!"
    assert response.headers == {
        "Content-Length": "13",
        "Content-Type": "text/plain; charset=utf-8",
    }


def test_response_html():
    response = httpx.Response(200, html="<html><body>Hello, world!</html></body>")

    assert response.status_code == 200
    assert response.reason_phrase == "OK"
    assert response.text == "<html><body>Hello, world!</html></body>"
    assert response.headers == {
        "Content-Length": "39",
        "Content-Type": "text/html; charset=utf-8",
    }


def test_response_json():
    response = httpx.Response(200, json={"hello": "world"})

    assert response.status_code == 200
    assert response.reason_phrase == "OK"
    assert response.json() == {"hello": "world"}
    assert response.headers == {
        "Content-Length": "18",
        "Content-Type": "application/json",
    }


def test_raise_for_status():
    request = httpx.Request("GET", "https://example.org")

    # 2xx status codes are not an error.
    response = httpx.Response(200, request=request)
    response.raise_for_status()

    # 4xx status codes are a client error.
    response = httpx.Response(403, request=request)
    with pytest.raises(httpx.HTTPStatusError):
        response.raise_for_status()

    # 5xx status codes are a server error.
    response = httpx.Response(500, request=request)
    with pytest.raises(httpx.HTTPStatusError):
        response.raise_for_status()

    # Calling .raise_for_status without setting a request instance is
    # not valid. Should raise a runtime error.
    response = httpx.Response(200)
    with pytest.raises(RuntimeError):
        response.raise_for_status()


def test_response_repr():
    response = httpx.Response(
        200,
        content=b"Hello, world!",
    )
    assert repr(response) == "<Response [200 OK]>"


def test_response_content_type_encoding():
    """
    Use the charset encoding in the Content-Type header if possible.
    """
    headers = {"Content-Type": "text-plain; charset=latin-1"}
    content = "Latin 1: ÿ".encode("latin-1")
    response = httpx.Response(
        200,
        content=content,
        headers=headers,
    )
    assert response.text == "Latin 1: ÿ"
    assert response.encoding == "latin-1"


def test_response_autodetect_encoding():
    """
    Autodetect encoding if there is no Content-Type header.
    """
    content = "おはようございます。".encode("utf-8")
    response = httpx.Response(
        200,
        content=content,
    )
    assert response.text == "おはようございます。"
    assert response.encoding is None


def test_response_fallback_to_autodetect():
    """
    Fallback to autodetection if we get an invalid charset in the Content-Type header.
    """
    headers = {"Content-Type": "text-plain; charset=invalid-codec-name"}
    content = "おはようございます。".encode("utf-8")
    response = httpx.Response(
        200,
        content=content,
        headers=headers,
    )
    assert response.text == "おはようございます。"
    assert response.encoding is None


def test_response_no_charset_with_ascii_content():
    """
    A response with ascii encoded content should decode correctly,
    even with no charset specified.
    """
    content = b"Hello, world!"
    headers = {"Content-Type": "text/plain"}
    response = httpx.Response(
        200,
        content=content,
        headers=headers,
    )
    assert response.status_code == 200
    assert response.encoding is None
    assert response.text == "Hello, world!"


def test_response_no_charset_with_utf8_content():
    """
    A response with UTF-8 encoded content should decode correctly,
    even with no charset specified.
    """
    content = "Unicode Snowman: ☃".encode("utf-8")
    headers = {"Content-Type": "text/plain"}
    response = httpx.Response(
        200,
        content=content,
        headers=headers,
    )
    assert response.text == "Unicode Snowman: ☃"
    assert response.encoding is None


def test_response_no_charset_with_iso_8859_1_content():
    """
    A response with ISO 8859-1 encoded content should decode correctly,
    even with no charset specified.
    """
    content = "Accented: Österreich".encode("iso-8859-1")
    headers = {"Content-Type": "text/plain"}
    response = httpx.Response(
        200,
        content=content,
        headers=headers,
    )
    assert response.text == "Accented: Österreich"
    assert response.encoding is None


def test_response_no_charset_with_cp_1252_content():
    """
    A response with Windows 1252 encoded content should decode correctly,
    even with no charset specified.
    """
    content = "Euro Currency: €".encode("cp1252")
    headers = {"Content-Type": "text/plain"}
    response = httpx.Response(
        200,
        content=content,
        headers=headers,
    )
    assert response.text == "Euro Currency: €"
    assert response.encoding is None


def test_response_non_text_encoding():
    """
    Default to apparent encoding for non-text content-type headers.
    """
    headers = {"Content-Type": "image/png"}
    response = httpx.Response(
        200,
        content=b"xyz",
        headers=headers,
    )
    assert response.text == "xyz"
    assert response.encoding is None


def test_response_set_explicit_encoding():
    headers = {
        "Content-Type": "text-plain; charset=utf-8"
    }  # Deliberately incorrect charset
    response = httpx.Response(
        200,
        content="Latin 1: ÿ".encode("latin-1"),
        headers=headers,
    )
    response.encoding = "latin-1"
    assert response.text == "Latin 1: ÿ"
    assert response.encoding == "latin-1"


def test_response_force_encoding():
    response = httpx.Response(
        200,
        content="Snowman: ☃".encode("utf-8"),
    )
    response.encoding = "iso-8859-1"
    assert response.status_code == 200
    assert response.reason_phrase == "OK"
    assert response.text == "Snowman: â\x98\x83"
    assert response.encoding == "iso-8859-1"


def test_read():
    response = httpx.Response(
        200,
        content=b"Hello, world!",
    )

    assert response.status_code == 200
    assert response.text == "Hello, world!"
    assert response.encoding is None
    assert response.is_closed

    content = response.read()

    assert content == b"Hello, world!"
    assert response.content == b"Hello, world!"
    assert response.is_closed


def test_empty_read():
    response = httpx.Response(200)

    assert response.status_code == 200
    assert response.text == ""
    assert response.encoding is None
    assert response.is_closed

    content = response.read()

    assert content == b""
    assert response.content == b""
    assert response.is_closed


@pytest.mark.asyncio
async def test_aread():
    response = httpx.Response(
        200,
        content=b"Hello, world!",
    )

    assert response.status_code == 200
    assert response.text == "Hello, world!"
    assert response.encoding is None
    assert response.is_closed

    content = await response.aread()

    assert content == b"Hello, world!"
    assert response.content == b"Hello, world!"
    assert response.is_closed


@pytest.mark.asyncio
async def test_empty_aread():
    response = httpx.Response(200)

    assert response.status_code == 200
    assert response.text == ""
    assert response.encoding is None
    assert response.is_closed

    content = await response.aread()

    assert content == b""
    assert response.content == b""
    assert response.is_closed


def test_iter_raw():
    response = httpx.Response(
        200,
        content=streaming_body(),
    )

    raw = b""
    for part in response.iter_raw():
        raw += part
    assert raw == b"Hello, world!"


def test_iter_raw_on_iterable():
    response = httpx.Response(
        200,
        content=StreamingBody(),
    )

    raw = b""
    for part in response.iter_raw():
        raw += part
    assert raw == b"Hello, world!"


def test_iter_raw_on_async():
    response = httpx.Response(
        200,
        content=async_streaming_body(),
    )

    with pytest.raises(RuntimeError):
        [part for part in response.iter_raw()]


def test_iter_raw_increments_updates_counter():
    response = httpx.Response(200, content=streaming_body())

    num_downloaded = response.num_bytes_downloaded
    for part in response.iter_raw():
        assert len(part) == (response.num_bytes_downloaded - num_downloaded)
        num_downloaded = response.num_bytes_downloaded


@pytest.mark.asyncio
async def test_aiter_raw():
    response = httpx.Response(200, content=async_streaming_body())

    raw = b""
    async for part in response.aiter_raw():
        raw += part
    assert raw == b"Hello, world!"


@pytest.mark.asyncio
async def test_aiter_raw_on_sync():
    response = httpx.Response(
        200,
        content=streaming_body(),
    )

    with pytest.raises(RuntimeError):
        [part async for part in response.aiter_raw()]


@pytest.mark.asyncio
async def test_aiter_raw_increments_updates_counter():
    response = httpx.Response(200, content=async_streaming_body())

    num_downloaded = response.num_bytes_downloaded
    async for part in response.aiter_raw():
        assert len(part) == (response.num_bytes_downloaded - num_downloaded)
        num_downloaded = response.num_bytes_downloaded


def test_iter_bytes():
    response = httpx.Response(
        200,
        content=b"Hello, world!",
    )

    content = b""
    for part in response.iter_bytes():
        content += part
    assert content == b"Hello, world!"


@pytest.mark.asyncio
async def test_aiter_bytes():
    response = httpx.Response(
        200,
        content=b"Hello, world!",
    )

    content = b""
    async for part in response.aiter_bytes():
        content += part
    assert content == b"Hello, world!"


def test_iter_text():
    response = httpx.Response(
        200,
        content=b"Hello, world!",
    )

    content = ""
    for part in response.iter_text():
        content += part
    assert content == "Hello, world!"


@pytest.mark.asyncio
async def test_aiter_text():
    response = httpx.Response(
        200,
        content=b"Hello, world!",
    )

    content = ""
    async for part in response.aiter_text():
        content += part
    assert content == "Hello, world!"


def test_iter_lines():
    response = httpx.Response(
        200,
        content=b"Hello,\nworld!",
    )

    content = []
    for line in response.iter_lines():
        content.append(line)
    assert content == ["Hello,\n", "world!"]


@pytest.mark.asyncio
async def test_aiter_lines():
    response = httpx.Response(
        200,
        content=b"Hello,\nworld!",
    )

    content = []
    async for line in response.aiter_lines():
        content.append(line)
    assert content == ["Hello,\n", "world!"]


def test_sync_streaming_response():
    response = httpx.Response(
        200,
        content=streaming_body(),
    )

    assert response.status_code == 200
    assert not response.is_closed

    content = response.read()

    assert content == b"Hello, world!"
    assert response.content == b"Hello, world!"
    assert response.is_closed


@pytest.mark.asyncio
async def test_async_streaming_response():
    response = httpx.Response(
        200,
        content=async_streaming_body(),
    )

    assert response.status_code == 200
    assert not response.is_closed

    content = await response.aread()

    assert content == b"Hello, world!"
    assert response.content == b"Hello, world!"
    assert response.is_closed


def test_cannot_read_after_stream_consumed():
    response = httpx.Response(
        200,
        content=streaming_body(),
    )

    content = b""
    for part in response.iter_bytes():
        content += part

    with pytest.raises(httpx.StreamConsumed):
        response.read()


@pytest.mark.asyncio
async def test_cannot_aread_after_stream_consumed():
    response = httpx.Response(
        200,
        content=async_streaming_body(),
    )

    content = b""
    async for part in response.aiter_bytes():
        content += part

    with pytest.raises(httpx.StreamConsumed):
        await response.aread()


def test_cannot_read_after_response_closed():
    response = httpx.Response(
        200,
        content=streaming_body(),
    )

    response.close()
    with pytest.raises(httpx.ResponseClosed):
        response.read()


@pytest.mark.asyncio
async def test_cannot_aread_after_response_closed():
    response = httpx.Response(
        200,
        content=async_streaming_body(),
    )

    await response.aclose()
    with pytest.raises(httpx.ResponseClosed):
        await response.aread()


@pytest.mark.asyncio
async def test_elapsed_not_available_until_closed():
    response = httpx.Response(
        200,
        content=async_streaming_body(),
    )

    with pytest.raises(RuntimeError):
        response.elapsed


def test_unknown_status_code():
    response = httpx.Response(
        600,
    )
    assert response.status_code == 600
    assert response.reason_phrase == ""
    assert response.text == ""


def test_json_with_specified_encoding():
    data = {"greeting": "hello", "recipient": "world"}
    content = json.dumps(data).encode("utf-16")
    headers = {"Content-Type": "application/json, charset=utf-16"}
    response = httpx.Response(
        200,
        content=content,
        headers=headers,
    )
    assert response.json() == data


def test_json_with_options():
    data = {"greeting": "hello", "recipient": "world", "amount": 1}
    content = json.dumps(data).encode("utf-16")
    headers = {"Content-Type": "application/json, charset=utf-16"}
    response = httpx.Response(
        200,
        content=content,
        headers=headers,
    )
    assert response.json(parse_int=str)["amount"] == "1"


def test_json_without_specified_encoding():
    data = {"greeting": "hello", "recipient": "world"}
    content = json.dumps(data).encode("utf-32-be")
    headers = {"Content-Type": "application/json"}
    response = httpx.Response(
        200,
        content=content,
        headers=headers,
    )
    assert response.json() == data


def test_json_without_specified_encoding_decode_error():
    data = {"greeting": "hello", "recipient": "world"}
    content = json.dumps(data).encode("utf-32-be")
    headers = {"Content-Type": "application/json"}
    # force incorrect guess from `guess_json_utf` to trigger error
    with mock.patch("httpx._models.guess_json_utf", return_value="utf-32"):
        response = httpx.Response(
            200,
            content=content,
            headers=headers,
        )
        with pytest.raises(json.decoder.JSONDecodeError):
            response.json()


def test_json_without_specified_encoding_value_error():
    data = {"greeting": "hello", "recipient": "world"}
    content = json.dumps(data).encode("utf-32-be")
    headers = {"Content-Type": "application/json"}
    # force incorrect guess from `guess_json_utf` to trigger error
    with mock.patch("httpx._models.guess_json_utf", return_value="utf-32"):
        response = httpx.Response(200, content=content, headers=headers)
        with pytest.raises(ValueError):
            response.json()


@pytest.mark.parametrize(
    "headers, expected",
    [
        (
            {"Link": "<https://example.com>; rel='preload'"},
            {"preload": {"rel": "preload", "url": "https://example.com"}},
        ),
        (
            {"Link": '</hub>; rel="hub", </resource>; rel="self"'},
            {
                "hub": {"url": "/hub", "rel": "hub"},
                "self": {"url": "/resource", "rel": "self"},
            },
        ),
    ],
)
def test_link_headers(headers, expected):
    response = httpx.Response(
        200,
        content=None,
        headers=headers,
    )
    assert response.links == expected


@pytest.mark.parametrize("header_value", (b"deflate", b"gzip", b"br"))
def test_decode_error_with_request(header_value):
    headers = [(b"Content-Encoding", header_value)]
    body = b"test 123"
    compressed_body = brotli.compress(body)[3:]
    with pytest.raises(ValueError):
        httpx.Response(
            200,
            headers=headers,
            content=compressed_body,
        )

    with pytest.raises(httpx.DecodingError):
        httpx.Response(
            200,
            headers=headers,
            content=compressed_body,
            request=httpx.Request("GET", "https://www.example.org/"),
        )


@pytest.mark.parametrize("header_value", (b"deflate", b"gzip", b"br"))
def test_value_error_without_request(header_value):
    headers = [(b"Content-Encoding", header_value)]
    body = b"test 123"
    compressed_body = brotli.compress(body)[3:]
    with pytest.raises(ValueError):
        httpx.Response(200, headers=headers, content=compressed_body)


def test_response_with_unset_request():
    response = httpx.Response(200, content=b"Hello, world!")

    assert response.status_code == 200
    assert response.reason_phrase == "OK"
    assert response.text == "Hello, world!"
    assert not response.is_error


def test_set_request_after_init():
    response = httpx.Response(200, content=b"Hello, world!")

    response.request = httpx.Request("GET", "https://www.example.org")

    assert response.request.method == "GET"
    assert response.request.url == "https://www.example.org"


def test_cannot_access_unset_request():
    response = httpx.Response(200, content=b"Hello, world!")

    with pytest.raises(RuntimeError):
        response.request


def test_generator_with_transfer_encoding_header():
    def content():
        yield b"test 123"  # pragma: nocover

    response = httpx.Response(200, content=content())
    assert response.headers == {"Transfer-Encoding": "chunked"}


def test_generator_with_content_length_header():
    def content():
        yield b"test 123"  # pragma: nocover

    headers = {"Content-Length": "8"}
    response = httpx.Response(200, content=content(), headers=headers)
    assert response.headers == {"Content-Length": "8"}
