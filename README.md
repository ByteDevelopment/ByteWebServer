# ByteWebServer
It is designed to serve static websites and run PHP applications without requiring a full web server stack such as Apache or Nginx.

## ✨ Features

* 🚀 Lightweight Python HTTP server
* 🌐 Static file hosting
* 🐘 PHP CGI support
* 📄 Automatic `index.html` and `index.php` detection
* 🔒 Basic path traversal protection
* 🛡️ Protected file path handling
* ❌ Custom error pages
* 📦 Automatic PHP setup
* 🔍 MIME type detection
* 🧵 Multi-threaded client handling
* ⚡ Simple and easy to configure
* 🪟 Windows support

## 📁 Project Structure

```text
/
├── server.py
├── server.conf
├── www/
│   ├── index.html
│   └── index.php
├── errors/
│   ├── 403.html
│   ├── 404.html
│   ├── 429.html
│   └── 502.html
└── README.md
```

## 🚀 Getting Started

### Requirements

* Python 3.8+
* Windows
* PHP CGI (`php-cgi.exe`) for PHP support

### Run the Server

```bash
python server.py
```

The server will start on:

```text
http://localhost:80
```

If port `80` requires administrator privileges, change the port in `server.py`:

```python
PORT = 8080
```

Then open:

```text
http://localhost:8080
```

## 🐘 PHP Support

 supports PHP through PHP CGI.

Configure the PHP CGI executable in:

```python
PHP_CGI = r"C:\xampp\php\php-cgi.exe"
```

If PHP is not found, the server can automatically download and configure a PHP package.

## 🌐 Website Files

Place your website inside the `www` directory:

```text
www/
├── index.html
├── style.css
├── script.js
└── index.php
```

## 🔐 Security

 includes basic security protections such as:

* Path traversal prevention
* Unsafe path detection
* Query string validation
* CRLF request protection
* Restricted document root
* Safe PHP execution environment

>  is intended to be a lightweight development and personal hosting server. For production environments, a hardened web server such as Nginx or Apache is recommended.

## 📊 Server Response


```http
Server: ByteWebServer/1.1
X-Powered-By: ByteWebServer
```

## 🛠️ Configuration

Basic configuration can be changed directly in `server.py`:

```python
HOST = "0.0.0.0"
PORT = 80
WWW_DIR = "www"
PHP_CGI = r"C:\xampp\php\php-cgi.exe"
```

### Configuration

| Option    | Description            |
| --------- | ---------------------- |
| `HOST`    | Server bind address    |
| `PORT`    | HTTP port              |
| `WWW_DIR` | Website root directory |
| `PHP_CGI` | PHP CGI executable     |

## 📌 Roadmap

* [ ] HTTP/1.1 improvements
* [ ] Keep-Alive support
* [ ] Better request parsing
* [ ] Access logs
* [ ] Configuration file support
* [ ] HTTPS support
* [ ] Virtual hosts
* [ ] Upload support
* [ ] Better PHP CGI handling
* [ ] Rate limiting
* [ ] Admin dashboard

## 📜 License

This project is open-source. See the `LICENSE` file for details.

---

<p align="center">
  <b></b><br>
  A simple Python web server for everyone.
</p>
