import argparse
import importlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request
from flask import send_file, send_from_directory, url_for

from .page import SCHEMA


ENDPOINT_SCHEMA = "polyptich.www.endpoint"
RESTART_EXIT_CODE = 75
RESTART_CHILD_ENV = "POLYPTICH_WWW_RESTART_CHILD"


def create_app(root=".", allow_restart=True, restart_callback=None):
    app = Flask(__name__, static_folder=None)
    base_dir = (Path(root).resolve() / "www").resolve()
    restart_callback = restart_callback or _restart_process
    app.config["POLYPTICH_WWW_ENDPOINT_PARENTS"] = {}

    def safe_path(subpath=""):
        target = (base_dir / subpath).resolve()
        if target != base_dir and base_dir not in target.parents:
            abort(403)
        if _has_symlink(base_dir, target):
            abort(403)
        return target

    def report_manifest(path):
        manifest = read_manifest(path)
        if manifest is None or manifest.get("schema") != SCHEMA:
            return None
        return manifest

    def endpoint_manifest(path):
        manifest = read_manifest(path)
        if manifest is None or manifest.get("schema") != ENDPOINT_SCHEMA:
            return None
        return manifest

    def read_manifest(path):
        manifest_path = path / "manifest.json"
        if not path.is_dir() or not manifest_path.exists():
            return None
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            return None
        return manifest

    @app.route("/")
    @app.route("/browse/")
    @app.route("/browse/<path:subpath>")
    def browse(subpath=""):
        current = safe_path(subpath)
        query = request.args.get("q", "").strip()

        if not current.is_dir():
            abort(404)

        manifest = report_manifest(current)
        if manifest is not None and request.args.get("browse") != "1":
            return render_report(subpath)
        endpoint = endpoint_manifest(current)
        if endpoint is not None and request.args.get("browse") != "1":
            return redirect(_endpoint_href(subpath))

        items = []
        for path in sorted(current.iterdir(), key=_sort_key):
            if path.is_symlink():
                continue
            if query and query.lower() not in path.name.lower():
                continue

            rel = path.relative_to(base_dir).as_posix()
            item_manifest = report_manifest(path)
            item_endpoint = endpoint_manifest(path)
            is_dir = path.is_dir()
            is_html = path.is_file() and path.suffix.lower() == ".html"
            items.append(
                {
                    "name": path.name,
                    "path": rel,
                    "display_name": f"{path.name}/" if is_dir else path.name,
                    "is_dir": is_dir,
                    "is_report": item_manifest is not None or item_endpoint is not None,
                    "is_html": is_html,
                    "icon": _item_icon(item_manifest or item_endpoint, is_dir, is_html),
                    "kind": _item_kind(item_manifest, item_endpoint, is_dir, path),
                    "size": _format_size(None if is_dir else path.stat().st_size),
                    "modified": _format_mtime(path),
                    "href": _item_href(rel, item_manifest, item_endpoint, is_dir),
                    "delete_href": url_for("delete_item", subpath=rel),
                    "browse_href": url_for("browse", subpath=rel, browse=1)
                    if item_manifest is not None or item_endpoint is not None
                    else None,
                }
            )

        parent = None
        if current != base_dir:
            parent = current.parent.relative_to(base_dir).as_posix()

        return render_template(
            "browser.html",
            items=items,
            subpath=subpath,
            parent=parent,
            breadcrumbs=_build_breadcrumbs(subpath),
            base_dir=base_dir,
            item_count=len(items),
            query=query,
            allow_restart=app.config["POLYPTICH_WWW_ALLOW_RESTART"],
        )

    @app.route("/files/")
    @app.route("/files/<path:filename>")
    def download(filename=""):
        target = safe_path(filename)
        if target.is_dir():
            return browse(filename)
        if not target.exists():
            abort(404)
        return send_from_directory(base_dir, filename, as_attachment=False)

    @app.route("/delete/<path:subpath>", methods=["POST"])
    def delete_item(subpath):
        target = safe_path(subpath)
        if target == base_dir:
            abort(400)
        if not target.exists():
            abort(404)
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

        parent = target.parent.relative_to(base_dir).as_posix()
        if parent == ".":
            parent = ""
        return redirect(url_for("browse", subpath=parent))

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/restart", methods=["POST"])
    def restart():
        if not app.config["POLYPTICH_WWW_ALLOW_RESTART"]:
            abort(404)
        threading.Timer(0.2, restart_callback).start()
        return jsonify({"status": "restarting"})

    @app.route("/report/<path:subpath>")
    def render_report(subpath):
        current = safe_path(subpath)
        manifest = report_manifest(current)
        if manifest is None:
            abort(404)
        html = current / "index.html"
        if not html.exists():
            abort(404)
        base_href = url_for("download", filename=subpath.rstrip("/") + "/")
        content = html.read_text().replace("<head>", f'<head>\n  <base href="{base_href}">', 1)
        return app.response_class(content, mimetype="text/html")

    @app.route("/report-data/<path:subpath>/<component_id>")
    def report_data(subpath, component_id):
        current = safe_path(subpath)
        manifest = report_manifest(current)
        if manifest is None:
            abort(404)
        component = manifest.get("assets", {}).get(component_id)
        if component is None:
            abort(404)
        asset = safe_path(str(Path(subpath) / component["asset"]))
        if component["type"] == "table":
            pd = _require_pandas()
            return jsonify(pd.read_parquet(asset).to_dict(orient="records"))
        if component["type"] == "plotly":
            return send_from_directory(
                base_dir,
                str(asset.relative_to(base_dir)),
                as_attachment=False,
            )
        abort(404)

    @app.route("/report-download/<path:subpath>/<component_id>.xlsx")
    def report_download(subpath, component_id):
        current = safe_path(subpath)
        manifest = report_manifest(current)
        if manifest is None:
            abort(404)
        component = manifest.get("assets", {}).get(component_id)
        if component is None or component.get("type") != "table":
            abort(404)
        pd = _require_pandas()
        asset = safe_path(str(Path(subpath) / component["asset"]))
        output = BytesIO()
        pd.read_parquet(asset).to_excel(output, index=False)
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{component_id}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @app.route("/static/<path:filename>")
    def static_files(filename):
        response = send_from_directory(Path(__file__).parent / "static", filename, as_attachment=False)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.after_request
    def add_endpoint_browser_banner(response):
        if response.status_code != 200 or response.mimetype != "text/html" or response.is_streamed:
            return response
        parent = _endpoint_parent_for_request(app.config["POLYPTICH_WWW_ENDPOINT_PARENTS"], request.path)
        if parent is None:
            return response

        parent_href = url_for("browse", subpath=parent) if parent else url_for("browse")
        parent_label = "/" + parent if parent else "/"
        banner = _endpoint_browser_banner(parent_href, parent_label)
        content = response.get_data(as_text=True)
        if "data-endpoint-browser-banner" in content:
            return response
        if "<body" in content:
            marker = content.find(">", content.find("<body")) + 1
            content = content[:marker] + "\n" + banner + content[marker:]
        else:
            content = banner + content
        response.set_data(content)
        return response

    @app.errorhandler(404)
    def not_found(_error):
        return (
            render_template(
                "404.html",
                path=request.path,
                root_href="/",
            ),
            404,
        )

    _register_endpoint_manifests(app, base_dir)

    app.config["POLYPTICH_WWW_BASE_DIR"] = base_dir
    app.config["POLYPTICH_WWW_ALLOW_RESTART"] = allow_restart
    return app


def _restart_process():
    os._exit(RESTART_EXIT_CODE)


def _has_symlink(base_dir, target):
    try:
        relative = target.relative_to(base_dir)
    except ValueError:
        return True
    current = base_dir
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _sort_key(path):
    manifest = path / "manifest.json"
    is_report = path.is_dir() and manifest.exists()
    return (
        not is_report,
        not path.is_dir(),
        0 if path.suffix.lower() == ".html" else 1,
        path.name.lower(),
    )


def _item_icon(manifest, is_dir, is_html):
    if manifest is not None:
        return "report"
    if is_dir:
        return "folder"
    if is_html:
        return "html"
    return "file"


def _item_kind(manifest, endpoint, is_dir, path):
    if manifest is not None:
        return "polyptich report"
    if endpoint is not None:
        return "polyptich endpoint"
    if is_dir:
        return "directory"
    return path.suffix.lower().lstrip(".") or "file"


def _item_href(rel, manifest, endpoint, is_dir):
    if manifest is not None:
        return url_for("render_report", subpath=rel)
    if endpoint is not None:
        return _endpoint_href(rel)
    if is_dir:
        return url_for("browse", subpath=rel)
    return url_for("download", filename=rel)


def _endpoint_href(rel):
    return "/endpoint/" + rel.strip("/") + "/"


def _register_endpoint_manifests(app, base_dir):
    if not base_dir.exists():
        return
    for manifest_path in sorted(base_dir.rglob("manifest.json")):
        path = manifest_path.parent
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            continue
        if manifest.get("schema") != ENDPOINT_SCHEMA:
            continue
        rel = path.relative_to(base_dir).as_posix()
        parent = path.parent.relative_to(base_dir).as_posix()
        if parent == ".":
            parent = ""
        app.config["POLYPTICH_WWW_ENDPOINT_PARENTS"][_endpoint_href(rel)] = parent
        handler_path = manifest.get("handler")
        if not handler_path:
            raise ValueError(f"{manifest_path} is missing an endpoint handler")
        handler_class = _load_handler(handler_path, path)
        handler = handler_class(path=path, mount_path=rel, manifest=manifest)
        endpoint_name = "www_endpoint_" + rel.replace("/", "_").replace("-", "_")
        handler.register(app, mount_url=_endpoint_href(rel).rstrip("/"), endpoint_name=endpoint_name)


def _endpoint_parent_for_request(endpoint_parents, request_path):
    path = request_path if request_path.endswith("/") else request_path + "/"
    for prefix, parent in sorted(endpoint_parents.items(), key=lambda item: len(item[0]), reverse=True):
        if path.startswith(prefix):
            return parent
    return None


def _endpoint_browser_banner(parent_href, parent_label):
    return f"""<details class="endpoint-browser-banner" data-endpoint-browser-banner>
  <summary>Endpoint navigation</summary>
  <div class="endpoint-browser-banner-body">
    <span>Parent folder <code>{escape(parent_label)}</code></span>
    <a class="www-button www-button-secondary" href="{escape(parent_href, quote=True)}">Open in file browser</a>
  </div>
</details>"""


def _load_handler(handler_path, root_path):
    module_path, _, class_name = handler_path.partition(":")
    if not class_name:
        raise ValueError("Endpoint handler must be formatted as 'module:Class'.")
    if module_path.endswith(".py"):
        path = (root_path / module_path).resolve()
        spec = importlib.util.spec_from_file_location(f"polyptich_www_endpoint_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(module_path)
    handler = module
    for part in class_name.split("."):
        handler = getattr(handler, part)
    return handler


def _format_size(size):
    if size is None:
        return "directory"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _format_mtime(path):
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def _build_breadcrumbs(subpath):
    breadcrumbs = [{"label": "www", "path": ""}]
    current_parts = []
    for part in Path(subpath).parts:
        if part in {"", "."}:
            continue
        current_parts.append(part)
        breadcrumbs.append({"label": part, "path": "/".join(current_parts)})
    return breadcrumbs


def _require_pandas():
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("Install pandas to serve polyptich www tables.") from exc
    return pd


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Serve a polyptich www directory.")
    parser.add_argument("root", nargs="?", default=".", help="Directory containing a www folder")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5002")))
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--no-restart", action="store_true", help="Disable the browser restart button and endpoint")
    args = parser.parse_args(argv)

    if args.no_restart or os.environ.get(RESTART_CHILD_ENV) == "1":
        return _serve(args)
    return _restart_loop(argv)


def _serve(args):
    app = create_app(args.root, allow_restart=not args.no_restart)
    print(f"Hostname: {socket.getfqdn()}")
    print(f"Serving: {app.config['POLYPTICH_WWW_BASE_DIR']}")
    print(f"URL: http://{args.host}:{args.port}/")
    app.run(debug=args.debug, port=args.port, host=args.host, use_reloader=False)
    return 0


def _restart_loop(argv):
    command = [sys.executable, "-m", "polyptich.www.server"] + list(argv)
    env = dict(os.environ)
    env[RESTART_CHILD_ENV] = "1"
    while True:
        child = subprocess.Popen(command, env=env)
        try:
            exit_code = child.wait()
        except KeyboardInterrupt:
            child.terminate()
            child.wait()
            return 130
        if exit_code != RESTART_EXIT_CODE:
            return exit_code
        print("Restarting polyptich www server...", flush=True)


if __name__ == "__main__":
    sys.exit(main())
