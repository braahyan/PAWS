from nose.tools import *
import paws.main


def test_get_path_segments_works_on_well_formed_string():
    segments = paws.main.get_path_segments("/foo/bar/baz")
    assert segments == ["foo", "bar", "baz"]


def test_get_path_segments_returns_empty_on_empty_string():
    segments = paws.main.get_path_segments("")
    assert segments == []


def test_get_resource_by_path_works_on_well_formed_list():
    resources = [
        {"path": "/foo"}
    ]
    assert paws.main.get_resource_by_path("/foo", resources) == \
        {"path": "/foo"}


def test_get_resource_by_path_returns_none_on_not_found():
    resources = [
        {"path": "/foo"}
    ]
    assert paws.main.get_resource_by_path("/asdfasdf", resources) == \
        None


def test_get_resources_to_delete():
    resources = [
        {"path": "/foo/bar/baz", "id": "quuxqwert"},
        {"path": "/foo", "id": "asdfdkfkdk"},
        {"path": "/", "id": "foobar"}
    ]
    assert paws.main.get_resources_to_delete(resources) == \
        ["asdfdkfkdk"]


def test_get_resources_to_create():
    resources = [
        {"path": "/foo/bar/baz", "id": "quuxqwert"},
        {"path": "/foo", "id": "asdfdkfkdk"},
        {"path": "/", "id": "foobar"}
    ]
    assert paws.main.get_resources_to_create("/asdf/qwerty", resources) == \
        ("foobar", ["asdf", "qwerty"])
