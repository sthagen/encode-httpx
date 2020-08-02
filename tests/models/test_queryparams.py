import pytest

from httpx import QueryParams


@pytest.mark.parametrize(
    "source",
    [
        "a=123&a=456&b=789",
        {"a": ["123", "456"], "b": 789},
        {"a": ("123", "456"), "b": 789},
    ],
)
def test_queryparams(source):
    q = QueryParams(source)
    assert "a" in q
    assert "A" not in q
    assert "c" not in q
    assert q["a"] == "456"
    assert q.get("a") == "456"
    assert q.get("nope", default=None) is None
    assert q.get_list("a") == ["123", "456"]

    with pytest.warns(DeprecationWarning):
        assert q.getlist("a") == ["123", "456"]

    assert list(q.keys()) == ["a", "b"]
    assert list(q.values()) == ["456", "789"]
    assert list(q.items()) == [("a", "456"), ("b", "789")]
    assert len(q) == 2
    assert list(q) == ["a", "b"]
    assert dict(q) == {"a": "456", "b": "789"}
    assert str(q) == "a=123&a=456&b=789"
    assert repr(q) == "QueryParams('a=123&a=456&b=789')"
    assert QueryParams({"a": "123", "b": "456"}) == QueryParams(
        [("a", "123"), ("b", "456")]
    )
    assert QueryParams({"a": "123", "b": "456"}) == QueryParams("a=123&b=456")
    assert QueryParams({"a": "123", "b": "456"}) == QueryParams(
        {"b": "456", "a": "123"}
    )
    assert QueryParams() == QueryParams({})
    assert QueryParams([("a", "123"), ("a", "456")]) == QueryParams("a=123&a=456")
    assert QueryParams({"a": "123", "b": "456"}) != "invalid"

    q = QueryParams([("a", "123"), ("a", "456")])
    assert QueryParams(q) == q


def test_queryparam_types():
    q = QueryParams(None)
    assert str(q) == ""

    q = QueryParams({"a": True})
    assert str(q) == "a=true"

    q = QueryParams({"a": False})
    assert str(q) == "a=false"

    q = QueryParams({"a": ""})
    assert str(q) == "a="

    q = QueryParams({"a": None})
    assert str(q) == "a="

    q = QueryParams({"a": 1.23})
    assert str(q) == "a=1.23"

    q = QueryParams({"a": 123})
    assert str(q) == "a=123"

    q = QueryParams({"a": [1, 2]})
    assert str(q) == "a=1&a=2"


def test_queryparam_setters():
    q = QueryParams({"a": 1})
    q.update([])

    assert str(q) == "a=1"

    q = QueryParams([("a", 1), ("a", 2)])
    q["a"] = "3"
    assert str(q) == "a=3"

    q = QueryParams([("a", 1), ("b", 1)])
    u = QueryParams([("b", 2), ("b", 3)])
    q.update(u)

    assert str(q) == "a=1&b=2&b=3"
    assert q["b"] == u["b"]
