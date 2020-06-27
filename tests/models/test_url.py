import pytest

from httpx import URL, InvalidURL
from httpx._models import Origin


@pytest.mark.parametrize(
    "given,idna,host,scheme,port",
    [
        (
            "http://中国.icom.museum:80/",
            "http://xn--fiqs8s.icom.museum:80/",
            "xn--fiqs8s.icom.museum",
            "http",
            80,
        ),
        (
            "http://Königsgäßchen.de",
            "http://xn--knigsgchen-b4a3dun.de",
            "xn--knigsgchen-b4a3dun.de",
            "http",
            80,
        ),
        ("https://faß.de", "https://xn--fa-hia.de", "xn--fa-hia.de", "https", 443),
        (
            "https://βόλος.com:443",
            "https://xn--nxasmm1c.com:443",
            "xn--nxasmm1c.com",
            "https",
            443,
        ),
        (
            "http://ශ්‍රී.com:444",
            "http://xn--10cl1a0b660p.com:444",
            "xn--10cl1a0b660p.com",
            "http",
            444,
        ),
        (
            "https://نامه‌ای.com:4433",
            "https://xn--mgba3gch31f060k.com:4433",
            "xn--mgba3gch31f060k.com",
            "https",
            4433,
        ),
    ],
    ids=[
        "http_with_port",
        "unicode_tr46_compat",
        "https_without_port",
        "https_with_port",
        "http_with_custom_port",
        "https_with_custom_port",
    ],
)
def test_idna_url(given, idna, host, scheme, port):
    url = URL(given)
    assert url == URL(idna)
    assert url.host == host
    assert url.scheme == scheme
    assert url.port == port


def test_url():
    url = URL("https://example.org:123/path/to/somewhere?abc=123#anchor")
    assert url.scheme == "https"
    assert url.host == "example.org"
    assert url.port == 123
    assert url.authority == "example.org:123"
    assert url.path == "/path/to/somewhere"
    assert url.query == "abc=123"
    assert url.fragment == "anchor"
    assert (
        repr(url) == "URL('https://example.org:123/path/to/somewhere?abc=123#anchor')"
    )

    new = url.copy_with(scheme="http", port=None)
    assert new == URL("http://example.org/path/to/somewhere?abc=123#anchor")
    assert new.scheme == "http"


def test_url_eq_str():
    url = URL("https://example.org:123/path/to/somewhere?abc=123#anchor")
    assert url == "https://example.org:123/path/to/somewhere?abc=123#anchor"
    assert str(url) == url


def test_url_params():
    url = URL("https://example.org:123/path/to/somewhere", params={"a": "123"})
    assert str(url) == "https://example.org:123/path/to/somewhere?a=123"

    url = URL("https://example.org:123/path/to/somewhere?b=456", params={"a": "123"})
    assert str(url) == "https://example.org:123/path/to/somewhere?b=456&a=123"


def test_url_join():
    """
    Some basic URL joining tests.
    """
    url = URL("https://example.org:123/path/to/somewhere")
    assert url.join("/somewhere-else") == "https://example.org:123/somewhere-else"
    assert (
        url.join("somewhere-else") == "https://example.org:123/path/to/somewhere-else"
    )
    assert (
        url.join("../somewhere-else") == "https://example.org:123/path/somewhere-else"
    )
    assert url.join("../../somewhere-else") == "https://example.org:123/somewhere-else"


def test_url_join_rfc3986():
    """
    URL joining tests, as-per reference examples in RFC 3986.

    https://tools.ietf.org/html/rfc3986#section-5.4
    """

    url = URL("http://example.com/b/c/d;p?q")

    with pytest.raises(InvalidURL):
        assert url.join("g:h") == "g:h"

    assert url.join("g") == "http://example.com/b/c/g"
    assert url.join("./g") == "http://example.com/b/c/g"
    assert url.join("g/") == "http://example.com/b/c/g/"
    assert url.join("/g") == "http://example.com/g"
    assert url.join("//g") == "http://g"
    assert url.join("?y") == "http://example.com/b/c/d;p?y"
    assert url.join("g?y") == "http://example.com/b/c/g?y"
    assert url.join("#s") == "http://example.com/b/c/d;p?q#s"
    assert url.join("g#s") == "http://example.com/b/c/g#s"
    assert url.join("g?y#s") == "http://example.com/b/c/g?y#s"
    assert url.join(";x") == "http://example.com/b/c/;x"
    assert url.join("g;x") == "http://example.com/b/c/g;x"
    assert url.join("g;x?y#s") == "http://example.com/b/c/g;x?y#s"
    assert url.join("") == "http://example.com/b/c/d;p?q"
    assert url.join(".") == "http://example.com/b/c/"
    assert url.join("./") == "http://example.com/b/c/"
    assert url.join("..") == "http://example.com/b/"
    assert url.join("../") == "http://example.com/b/"
    assert url.join("../g") == "http://example.com/b/g"
    assert url.join("../..") == "http://example.com/"
    assert url.join("../../") == "http://example.com/"
    assert url.join("../../g") == "http://example.com/g"

    assert url.join("../../../g") == "http://example.com/g"
    assert url.join("../../../../g") == "http://example.com/g"

    assert url.join("/./g") == "http://example.com/g"
    assert url.join("/../g") == "http://example.com/g"
    assert url.join("g.") == "http://example.com/b/c/g."
    assert url.join(".g") == "http://example.com/b/c/.g"
    assert url.join("g..") == "http://example.com/b/c/g.."
    assert url.join("..g") == "http://example.com/b/c/..g"

    assert url.join("./../g") == "http://example.com/b/g"
    assert url.join("./g/.") == "http://example.com/b/c/g/"
    assert url.join("g/./h") == "http://example.com/b/c/g/h"
    assert url.join("g/../h") == "http://example.com/b/c/h"
    assert url.join("g;x=1/./y") == "http://example.com/b/c/g;x=1/y"
    assert url.join("g;x=1/../y") == "http://example.com/b/c/y"

    assert url.join("g?y/./x") == "http://example.com/b/c/g?y/./x"
    assert url.join("g?y/../x") == "http://example.com/b/c/g?y/../x"
    assert url.join("g#s/./x") == "http://example.com/b/c/g#s/./x"
    assert url.join("g#s/../x") == "http://example.com/b/c/g#s/../x"


def test_url_set():
    urls = (
        URL("http://example.org:123/path/to/somewhere"),
        URL("http://example.org:123/path/to/somewhere/else"),
    )

    url_set = set(urls)

    assert all(url in urls for url in url_set)


def test_url_full_path_setter():
    url = URL("http://example.org")

    url.full_path = "http://example.net"
    assert url.full_path == "http://example.net"


def test_origin_from_url_string():
    origin = Origin("https://example.com")
    assert origin.scheme == "https"
    assert origin.is_ssl
    assert origin.host == "example.com"
    assert origin.port == 443


def test_origin_repr():
    origin = Origin("https://example.com:8080")
    assert str(origin) == "Origin(scheme='https' host='example.com' port=8080)"


def test_origin_equal():
    origin1 = Origin("https://example.com")
    origin2 = Origin("https://example.com")
    assert origin1 is not origin2
    assert origin1 == origin2
    assert len({origin1, origin2}) == 1


def test_url_copywith_for_authority():
    copy_with_kwargs = {
        "username": "username",
        "password": "password",
        "port": 444,
        "host": "example.net",
    }
    url = URL("https://example.org")
    new = url.copy_with(**copy_with_kwargs)
    for k, v in copy_with_kwargs.items():
        assert getattr(new, k) == v
    assert str(new) == "https://username:password@example.net:444"
