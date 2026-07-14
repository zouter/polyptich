import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


def load_create_app():
    pytest.importorskip("flask")
    root = Path(__file__).parents[1]
    package = types.ModuleType("polyptich")
    package.__path__ = [str(root / "src" / "polyptich")]
    www_package = types.ModuleType("polyptich.www")
    www_package.__path__ = [str(root / "src" / "polyptich" / "www")]
    sys.modules.setdefault("polyptich", package)
    sys.modules.setdefault("polyptich.www", www_package)

    page_path = root / "src" / "polyptich" / "www" / "page.py"
    page_spec = importlib.util.spec_from_file_location("polyptich.www.page", page_path)
    page_module = importlib.util.module_from_spec(page_spec)
    sys.modules["polyptich.www.page"] = page_module
    page_spec.loader.exec_module(page_module)

    path = root / "src" / "polyptich" / "www" / "server.py"
    spec = importlib.util.spec_from_file_location("polyptich.www.server", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["polyptich.www.server"] = module
    spec.loader.exec_module(module)
    return module.create_app


def load_overview_grid():
    root = Path(__file__).parents[1]
    package = types.ModuleType("polyptich")
    package.__path__ = [str(root / "src" / "polyptich")]
    www_package = types.ModuleType("polyptich.www")
    www_package.__path__ = [str(root / "src" / "polyptich" / "www")]
    sys.modules.setdefault("polyptich", package)
    sys.modules.setdefault("polyptich.www", www_package)

    path = root / "src" / "polyptich" / "www" / "overview.py"
    spec = importlib.util.spec_from_file_location("polyptich.www.overview", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["polyptich.www.overview"] = module
    spec.loader.exec_module(module)
    return module.OverviewGrid


def test_custom_endpoint_manifest_registers_local_handler(tmp_path):
    create_app = load_create_app()
    endpoint = tmp_path / "www" / "custom"
    endpoint.mkdir(parents=True)
    (endpoint / "custom_endpoint.py").write_text(
        "class CustomEndpoint:\n"
        "    def __init__(self, path, mount_path, manifest):\n"
        "        self.manifest = manifest\n"
        "    def register(self, app, mount_url, endpoint_name):\n"
        "        app.add_url_rule(mount_url + '/', endpoint_name, self.index)\n"
        "    def index(self):\n"
        "        return 'hello ' + self.manifest['title']\n"
    )
    (endpoint / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "polyptich.www.endpoint",
                "schema_version": 1,
                "handler": "custom_endpoint.py:CustomEndpoint",
                "title": "Endpoint",
            }
        )
    )

    client = create_app(tmp_path).test_client()

    response = client.get("/endpoint/custom/")
    assert b"hello Endpoint" in response.data
    assert b"data-endpoint-browser-banner" in response.data
    assert b'href="/browse/"' in response.data
    assert client.get("/browse/custom").status_code == 302


def test_endpoint_banner_links_to_parent_folder(tmp_path):
    create_app = load_create_app()
    endpoint = tmp_path / "www" / "parent" / "custom"
    endpoint.mkdir(parents=True)
    (endpoint / "custom_endpoint.py").write_text(
        "class CustomEndpoint:\n"
        "    def __init__(self, path, mount_path, manifest):\n"
        "        pass\n"
        "    def register(self, app, mount_url, endpoint_name):\n"
        "        app.add_url_rule(mount_url + '/', endpoint_name, self.index)\n"
        "    def index(self):\n"
        "        return '<html><body>nested</body></html>'\n"
    )
    (endpoint / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "polyptich.www.endpoint",
                "schema_version": 1,
                "handler": "custom_endpoint.py:CustomEndpoint",
                "title": "Nested Endpoint",
            }
        )
    )

    response = create_app(tmp_path).test_client().get("/endpoint/parent/custom/")

    assert b"data-endpoint-browser-banner" in response.data
    assert b'href="/browse/parent"' in response.data
    assert response.data.index(b"data-endpoint-browser-banner") < response.data.index(b"nested")


def test_overview_grid_endpoint_filters_sorts_and_pages(tmp_path):
    OverviewGrid = load_overview_grid()
    grid = OverviewGrid(
        tmp_path / "www" / "overview",
        title="Datasets",
        filters=[{"key": "kind", "label": "Kind", "options": ["rna", "atac"]}, {"key": "cells", "label": "Cells", "type": "range"}],
        sorts=[{"key": "cells", "label": "Cells"}],
        page_size=1,
    )
    grid.add_item("B", "b.html", values={"kind": "rna", "cells": 20})
    grid.add_item("A", "a.html", values={"kind": "rna", "cells": 10})
    grid.add_item("C", "c.html", values={"kind": "atac", "cells": 30})

    client = load_create_app()(tmp_path).test_client()
    page = client.get("/endpoint/overview/")
    data = client.get("/endpoint/overview/items?f_kind=rna&sort=cells&order=asc&limit=1").get_json()

    assert page.status_code == 200
    assert b"polyptich-overview-config" in page.data
    assert b"data-endpoint-browser-banner" in page.data
    assert data["total"] == 2
    assert [item["title"] for item in data["items"]] == ["A"]


def test_missing_endpoint_renders_404_page_with_root_link(tmp_path):
    client = load_create_app()(tmp_path).test_client()

    response = client.get("/endpoint/does-not-exist/")

    assert response.status_code == 404
    assert b"Page not found" in response.data
    assert b'href="/"' in response.data
