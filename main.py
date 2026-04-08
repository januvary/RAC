#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC Entry Point (NiceGUI + PyWebView native window)
"""

import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _start_nicegui_server(port: int):
    from nicegui import ui, app
    from starlette.requests import Request
    from src.web.app import init_app, shutdown_app
    from src.web.pages.start_page import create_start_page
    from src.web.pages.entry_page import create_entry_page

    app.on_startup(init_app)
    app.on_shutdown(shutdown_app)

    @ui.page("/")
    def index():
        create_start_page()

    @ui.page("/entry/{tipo}")
    def entry(tipo: str, request: Request):
        create_entry_page(tipo, request)

    ui.run(
        title="RAC - Registros Alto Custo",
        dark=False,
        reload=False,
        port=port,
        show=False,
    )


def main():
    port = 8080

    server_thread = threading.Thread(
        target=_start_nicegui_server,
        args=(port,),
        daemon=True,
    )
    server_thread.start()

    for _ in range(30):
        time.sleep(0.5)
        import urllib.request
        try:
            urllib.request.urlopen(f"http://localhost:{port}/")
            break
        except Exception:
            continue

    import webview
    window = webview.create_window(
        "RAC - Registros Alto Custo",
        f"http://localhost:{port}",
        width=900,
        height=700,
        min_size=(750, 600),
        text_select=False,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
