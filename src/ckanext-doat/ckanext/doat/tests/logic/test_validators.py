"""Tests for validators.py."""

import pytest

import ckan.plugins.toolkit as tk

from ckanext.doat.logic import validators


def test_doat_reauired_with_valid_value():
    assert validators.doat_required("value") == "value"


def test_doat_reauired_with_invalid_value():
    with pytest.raises(tk.Invalid):
        validators.doat_required(None)
