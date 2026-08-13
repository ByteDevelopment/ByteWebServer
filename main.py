import socket
import os
import mimetypes
import subprocess
import configparser
import re
import urllib.request
import zipfile
import threading
import time

HOST = "0.0.0.0"
PORT = 80
WWW_DIR = "www"
PHP_CGI = "C:\\xampp\\php\\php-cgi.exe"

CONFIG_FILE = "server.conf"
ERROR_PAGES = {}

SERVER_HEADER = "Server: ByteWebServer/1.1\r\nX-Powered-By: ByteWebServer\r\n"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def secure_path(path):
    clean = os.path.normpath(path).replace("\\", "/")
    if ".." in clean or clean.startswith("/") or clean.startswith("\\"):
        return None
    
    banned = ["php://", "file://", "%2e%2e", "%2f", "%5c"]
    for b in banned:
        if b in clean.lower():
            return None
    return clean

def validate_query_string(qs):
    if re.match(r'^[A-Za-z0-9_\-&=]*$', qs):
        return qs
    return ""

def safe_path_check(path):
    return "\r" not in path and "\n" not in path

def auto_generate_error_pages():
    if not os.path.exists("errors"):
        os.makedirs("errors")

    default_errors = {
        "404.html": "<h1>404 - Page Not Found</h1>",
        "403.html": "<h1>403 - Forbidden</h1>",
        "502.html": "<h1>502 - Bad Gateway</h1>",
        "429.html": "<h1>429 - Too Many Requests</h1>"
    }

    for filename, html in default_errors.items():
        path = os.path.join("errors", filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)

def load_error_page(code):
    path = ERROR_PAGES.get(code)
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    default_path = os.path.join("errors", f"{code}.html")
    if os.path.exists(default_path):
        with open(default_path, "rb") as f:
            return f.read()
    return f"<h1>Error {code}</h1>".encode()

def run_php(script_path, method="GET", body=b"", query_string=""):
    script_path = os.path.abspath(script_path)
    env = os.environ.copy()
    
    env["PHPRC"] = os.path.dirname(PHP_CGI)
    env["GATEWAY_INTERFACE"] = "CGI/1.1"
    env["SERVER_PROTOCOL"] = "HTTP/1.1"
    env["REQUEST_METHOD"] = method
    env["SCRIPT_FILENAME"] = script_path
    env["DOCUMENT_ROOT"] = os.path.abspath(WWW_DIR)
    env["REDIRECT_STATUS"] = "200"
    env["QUERY_STRING"] = query_string
    
    if method == "POST":
        env["CONTENT_LENGTH"] = str(len(body))
        env["CONTENT_TYPE"] = "application/x-www-form-urlencoded"

    try:
        process = subprocess.Popen(
            [PHP_CGI],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=os.path.dirname(script_path)
        )
        output, error = process.communicate(input=body)
        if error.strip():
            return b"<h1>PHP ERROR</h1><pre>" + error + b"</pre>"
        if b"\r\n\r\n" in output:
            return output.split(b"\r\n\r\n", 1)[1]
        return output
    except Exception as e:
        return f"<h1>CGI Error</h1><p>{e}</p>".encode()

def handle_client(client, addr):
    try:
        request = client.recv(65535)
        if not request:
            client.close()
            return

        request_text = request.decode(errors="ignore")
        lines = request_text.splitlines()
        if not lines:
            client.close()
            return

        first_line = lines[0].split()
        if len(first_line) < 2:
            client.close()
            return

        method, path = first_line[0], first_line[1]
        current_time = time.strftime('%H:%M:%S')
        print(Colors.OKCYAN + f"[{current_time}] {addr[0]} - {method} {path}" + Colors.ENDC)

        query_string = ""
        if "?" in path:
            path, query_string = path.split("?", 1)
            query_string = validate_query_string(query_string)

        rel_path = path.lstrip("/")
        if rel_path == "": rel_path = "."
        
        file_path = os.path.join(WWW_DIR, rel_path)
        abs_path = os.path.abspath(file_path)

        if not abs_path.startswith(os.path.abspath(WWW_DIR)):
            body = load_error_page(403)
            client.send(b"HTTP/1.1 403 Forbidden\r\n\r\n" + body)
            client.close()
            return

        if os.path.isdir(abs_path):
            if not path.endswith('/'):
                client.send(f"HTTP/1.1 301 Moved Permanently\r\nLocation: {path}/\r\n\r\n".encode())
                client.close()
                return

            for idx in ["index.php", "index.html"]:
                if os.path.exists(os.path.join(abs_path, idx)):
                    abs_path = os.path.join(abs_path, idx)
                    break

        if os.path.exists(abs_path) and not os.path.isdir(abs_path):
            if abs_path.endswith(".php"):
                post_data = b""
                if method == "POST" and b"\r\n\r\n" in request:
                    post_data = request.split(b"\r\n\r\n", 1)[1]
                
                output = run_php(abs_path, method, post_data, query_string)
                header = f"HTTP/1.1 200 OK\r\n{SERVER_HEADER}Content-Type: text/html\r\nContent-Length: {len(output)}\r\n\r\n"
                client.send(header.encode() + output)
            else:
                mime = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"
                with open(abs_path, "rb") as f:
                    content = f.read()
                header = f"HTTP/1.1 200 OK\r\n{SERVER_HEADER}Content-Type: {mime}\r\nContent-Length: {len(content)}\r\n\r\n"
                client.send(header.encode() + content)
        else:
            body = load_error_page(404)
            client.send(b"HTTP/1.1 404 Not Found\r\n\r\n" + body)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

def check_and_install_php():
    global PHP_CGI  
    
    if not os.path.exists(PHP_CGI):
        print(Colors.WARNING + "⚠️ php-cgi.exe not found." + Colors.ENDC)
        choice = input("Download PHP? (y/n): ")
        if choice.lower() == 'y':
            try:
                print("⏳ Downloading...")
                urllib.request.urlretrieve("https://uploadkon.ir/uploads/143b13_26php.zip", "php.zip")
                with zipfile.ZipFile("php.zip", 'r') as zip_ref:
                    zip_ref.extractall("php_folder")
                os.remove("php.zip")
                PHP_CGI = os.path.abspath("php_folder/php-cgi.exe")
                print(Colors.OKGREEN + "✅ PHP Ready." + Colors.ENDC)
            except Exception as e:
                print(f"Fail: {e}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((HOST, PORT))
        server.listen(10)
        print(Colors.OKGREEN + f"🚀 Server: http://localhost:{PORT}" + Colors.ENDC)
        while True:
            c, addr = server.accept()
            threading.Thread(target=handle_client, args=(c, addr), daemon=True).start()
    except Exception as e:
        print(f"Server Error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    if not os.path.exists(WWW_DIR): os.makedirs(WWW_DIR)
    auto_generate_error_pages()
    check_and_install_php()
    start_server()
