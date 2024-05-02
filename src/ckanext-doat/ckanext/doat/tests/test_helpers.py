"""Tests for helpers.py."""

import ckanext.doat.helpers as helpers


def test_doat_hello():
    assert helpers.doat_hello() == "Hello, doat!"
