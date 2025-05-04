import logging
import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import datetime
import socket
from threading import Thread

dict_path = {
    '/': 'index.html',
    '/message.html': 'message.html'
}

BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '0.0.0.0'
SOCKET_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path in dict_path:
            self.send_html_file(dict_path.get(pr_url.path), 200)
        elif pathlib.Path().joinpath(pr_url.path[1:]).exists():
            self.send_static()
        else:
            self.send_html_file('error.html', 400)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        logging.info(f"Socket client started")
        socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_client.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        socket_client.close()
        logging.info(f"Socket client send data")
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def save_data(data_dict: bytes):
    file_name = 'storage/data.json'
    date_now = datetime.datetime.now().isoformat()
    data_parse = urllib.parse.unquote_plus(data_dict.decode())
    data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
    logging.info(f"Data: {data_dict}")
    dict_to_save = {date_now: data_dict}

    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            load_dict = json.load(f)
    except:
        load_dict = {}
    load_dict.update(dict_to_save)
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(load_dict, file, indent=6, ensure_ascii=False)


def socket_run(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info(f"Socket server started {host} {port}")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            save_data(msg)
    except KeyboardInterrupt:
        server_socket.close()


def run(host=HTTP_HOST, port=HTTP_PORT):
    server_address = (host, port)
    http = HTTPServer(server_address, HttpHandler)
    logging.info(f"HTTP server started {host} {port}")
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server = Thread(target=run, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=socket_run, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()
