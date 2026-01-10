import asyncio
import threading
import http.server
import socketserver
import os
from recorder import Runner
import logging

logging.basicConfig(level=logging.INFO)

PORT = 8085
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)


def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()


server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

workflow = [
    {"type": "click", "selector": "#open-popup"},
    {"type": "click", "selector": "#popup-button"},
    {"type": "click", "selector": "#final-button"},
]


async def run_test():
    print("Starting Runner Test...")
    runner = Runner()
    url = f"http://127.0.0.1:{PORT}/main_test.html"

    await runner.run_workflow(url, workflow)
    print("Test Complete.")


if __name__ == "__main__":
    asyncio.run(run_test())
