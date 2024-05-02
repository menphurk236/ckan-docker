"""Tests for views.py."""

import pytest

import ckanext.doat.validators as validators


import ckan.plugins.toolkit as tk


@pytest.mark.ckan_config("ckan.plugins", "doat")
@pytest.mark.usefixtures("with_plugins")
def test_doat_blueprint(app, reset_db):
    resp = app.get(tk.h.url_for("doat.page"))
    assert resp.status_code == 200
    assert resp.body == "Hello, doat!"
