import importlib.util
import json
import sys
import time
import types
from pathlib import Path

import pytest


def load_page_class():
    path = Path(__file__).parents[1] / "src" / "polyptich" / "www" / "page.py"
    spec = importlib.util.spec_from_file_location("polyptich_www_page", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Page


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


Page = load_page_class()


def read_manifest(path):
    return json.loads((path / "manifest.json").read_text())


def test_page_writes_manifest_immediately(tmp_path):
    page = Page(tmp_path / "www" / "report", title="Analysis")
    section = page.section("QC")
    section.add_html("<strong>ok</strong>", title="Summary")

    report = tmp_path / "www" / "report"
    manifest = read_manifest(report)
    assert manifest["schema"] == "polyptich.www.report"
    assert manifest["schema_version"] == 1
    assert manifest["title"] == "Analysis"
    assert "components" not in manifest
    html = (report / "index.html").read_text()
    assert 'id="qc"' in html
    assert "<strong>ok</strong>" in html


def test_overwrite_deletes_existing_folder(tmp_path):
    report = tmp_path / "www" / "report"
    report.mkdir(parents=True)
    (report / "unknown.txt").write_text("delete me")

    Page(report, title="Fresh", overwrite=True)

    assert not (report / "unknown.txt").exists()
    assert read_manifest(report)["title"] == "Fresh"


def test_index_html_is_rewritten_when_components_are_added(tmp_path):
    report = tmp_path / "www" / "report"
    page = Page(report, title="First")
    page.add_html("one", title="One")
    page.add_html("two", title="Two")

    html = (report / "index.html").read_text()
    assert html.index("one") < html.index("two")
    assert read_manifest(report)["assets"] == {}


def test_tabs_preserve_insertion_order(tmp_path):
    page = Page(tmp_path / "www" / "report")
    section = page.section("QC")
    tabs = section.tabs("Samples")
    tabs.add_tab("Sample A").add_html("a", title="Plot A")
    tabs.add_tab("Sample B").add_html("b", title="Plot B")

    html = (tmp_path / "www" / "report" / "index.html").read_text()
    assert html.index("Sample A") < html.index("Sample B")
    assert 'role="tab"' in html


def test_cards_can_contain_arbitrary_html_and_links(tmp_path):
    page = Page(tmp_path / "www" / "report")
    page.add_card('<img src="preview.png" alt="Preview"><p>open me</p>', title="Preview", href="../other/")

    html = (tmp_path / "www" / "report" / "index.html").read_text()
    assert '<a class="component card linked-card"' in html
    assert 'href="../other/"' in html
    assert '<img src="preview.png" alt="Preview">' in html


def test_dataframe_table_writes_parquet_with_index_columns(tmp_path):
    pd = pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")

    df = pd.DataFrame({"value": [1, 2]}, index=pd.Index(["a", "b"], name="cell"))
    Page(tmp_path / "www" / "report").add_table(df, title="Cells")

    manifest = read_manifest(tmp_path / "www" / "report")
    component = manifest["assets"]["cells"]
    assert component["type"] == "table"
    assert component["columns"] == ["cell", "value"]
    assert (tmp_path / "www" / "report" / component["asset"]).exists()
    assert not (tmp_path / "www" / "report" / "assets").exists()


def test_browser_deletes_file_after_post(tmp_path):
    create_app = load_create_app()
    target = tmp_path / "www" / "delete-me.txt"
    target.parent.mkdir()
    target.write_text("delete me")

    response = create_app(tmp_path).test_client().post("/delete/delete-me.txt")

    assert response.status_code == 302
    assert response.headers["Location"] == "/browse/"
    assert not target.exists()


def test_browser_deletes_folder_after_post(tmp_path):
    create_app = load_create_app()
    target = tmp_path / "www" / "delete-me"
    target.mkdir(parents=True)
    (target / "nested.txt").write_text("delete me")

    response = create_app(tmp_path).test_client().post("/delete/delete-me")

    assert response.status_code == 302
    assert response.headers["Location"] == "/browse/"
    assert not target.exists()


def test_health_endpoint_reports_ok(tmp_path):
    client = load_create_app()(tmp_path).test_client()

    response = client.get("/health")

    assert response.get_json() == {"status": "ok"}


def test_restart_endpoint_is_enabled_by_default(tmp_path):
    restarted = []
    client = load_create_app()(tmp_path, restart_callback=lambda: restarted.append(True)).test_client()

    response = client.post("/restart")
    time.sleep(0.3)

    assert response.get_json() == {"status": "restarting"}
    assert restarted == [True]


def test_restart_endpoint_can_be_disabled(tmp_path):
    client = load_create_app()(tmp_path, allow_restart=False, restart_callback=lambda: None).test_client()

    assert client.post("/restart").status_code == 404


def test_browser_shows_restart_and_health_by_default(tmp_path):
    (tmp_path / "www").mkdir()
    client = load_create_app()(tmp_path, restart_callback=lambda: None).test_client()

    response = client.get("/browse/")

    assert b"Server online" in response.data
    assert b"Restart server" in response.data


def test_browser_hides_restart_when_disabled(tmp_path):
    (tmp_path / "www").mkdir()
    client = load_create_app()(tmp_path, allow_restart=False, restart_callback=lambda: None).test_client()

    response = client.get("/browse/")

    assert b"Server online" in response.data
    assert b"Restart server" not in response.data


def test_missing_route_renders_404_page_with_root_link(tmp_path):
    (tmp_path / "www").mkdir()
    client = load_create_app()(tmp_path).test_client()

    response = client.get("/missing-page")

    assert response.status_code == 404
    assert b"Page not found" in response.data
    assert b"Go to site root" in response.data
    assert b'href="/"' in response.data
