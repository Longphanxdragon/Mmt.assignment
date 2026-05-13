#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

import asyncio
import inspect

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.

    The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
    dispatching them to appropriate route handlers, and constructing responses.
    It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
    and :class:`Response <Response>` objects for full request lifecycle management.

    Attributes:
        ip (str): IP address of the client.
        port (int): Port number of the client.
        conn (socket): Active socket connection.
        connaddr (tuple): Address of the connected client.
        routes (dict): Mapping of route paths to handler functions.
        request (Request): Request object for parsing incoming data.
        response (Response): Response object for building and sending replies.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.

        :param ip (str): IP address of the client.
        :param port (int): Port number of the client.
        :param conn (socket): Active socket connection.
        :param connaddr (tuple): Address of the connected client.
        :param routes (dict): Mapping of route paths to handler functions.
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def _cors_headers(self, origin="*"):
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Cookie",
            "Access-Control-Allow-Credentials": "true",
            "Vary": "Origin",
        }

    def _build_json_response(self, body_obj, status=200, extra_headers=None, origin="*"):
        import json

        if isinstance(body_obj, (bytes, bytearray)):
            body_bytes = bytes(body_obj)
        else:
            if not isinstance(body_obj, (str, dict, list)):
                body_obj = str(body_obj)
            body_text = json.dumps(body_obj) if isinstance(body_obj, (dict, list)) else str(body_obj)
            body_bytes = body_text.encode("utf-8")

        status_text = "OK" if int(status) == 200 else "ERROR"
        header_text = (
            f"HTTP/1.1 {status} {status_text}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
        )
        for key, value in self._cors_headers(origin=origin).items():
            header_text += f"{key}: {value}\r\n"
        for key, value in (extra_headers or {}).items():
            header_text += f"{key}: {value}\r\n"
        return header_text.encode("utf-8") + b"\r\n" + body_bytes

    def _build_options_response(self, origin="*"):
        header_text = "HTTP/1.1 204 No Content\r\nContent-Length: 0\r\n"
        for key, value in self._cors_headers(origin=origin).items():
            header_text += f"{key}: {value}\r\n"
        return header_text.encode("utf-8") + b"\r\n"

    def _content_length_from_request(self, request_text):
        for line in request_text.split("\r\n"):
            if line.lower().startswith("content-length:"):
                try:
                    return int(line.split(":", 1)[1].strip())
                except Exception:
                    return 0
        return 0

    def _read_full_request_sync(self, conn):
        data = b""
        header_end = -1
        content_length = None

        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break

            data += chunk

            if header_end == -1:
                header_end = data.find(b"\r\n\r\n")
                if header_end != -1:
                    header_text = data[:header_end].decode("utf-8", errors="replace")
                    content_length = self._content_length_from_request(header_text)

            if header_end != -1 and content_length is not None:
                total_needed = header_end + 4 + content_length
                if len(data) >= total_needed:
                    break

        return data.decode("utf-8", errors="replace")

    async def _read_full_request_async(self, reader):
        data = b""
        header_end = -1
        content_length = None

        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break

            data += chunk

            if header_end == -1:
                header_end = data.find(b"\r\n\r\n")
                if header_end != -1:
                    header_text = data[:header_end].decode("utf-8", errors="replace")
                    content_length = self._content_length_from_request(header_text)

            if header_end != -1 and content_length is not None:
                total_needed = header_end + 4 + content_length
                if len(data) >= total_needed:
                    break

        return data.decode("utf-8", errors="replace")

    def handle_client(self, conn, addr, routes):
        """Handle one client connection in blocking/threaded mode."""

        self.conn = conn
        req = self.request
        resp = self.response

        msg = self._read_full_request_sync(conn)
        req.prepare(msg, routes)
        print("[HttpAdapter] Invoke handle_client connection {}".format(addr))
        origin = req.headers.get("origin", "*") if req.headers else "*"

        if req.method == "OPTIONS":
            conn.sendall(self._build_options_response(origin=origin))
            conn.close()
            return

        if req.hook:
            hook_result = req.hook(headers=req.headers, body=req.body)
            if inspect.isawaitable(hook_result):
                hook_result = asyncio.run(hook_result)
            if isinstance(hook_result, tuple):
                body_obj, extra_headers, status = hook_result
                response = self._build_json_response(body_obj, status=status, extra_headers=extra_headers, origin=origin)
            else:
                response = self._build_json_response(hook_result, origin=origin)
        else:
            response = resp.build_response(req)

        conn.sendall(response)
        conn.close()

    async def handle_client_coroutine(self, reader, writer):
        """Handle one client connection in asyncio mode."""

        req = self.request
        resp = self.response

        addr = writer.get_extra_info("peername")
        print("[HttpAdapter] Invoke handle_client_coroutine connection {}".format(addr))

        msg = await self._read_full_request_async(reader)
        req.prepare(msg, routes=self.routes)
        origin = req.headers.get("origin", "*") if req.headers else "*"

        if req.method == "OPTIONS":
            writer.write(self._build_options_response(origin=origin))
            await writer.drain()
            return

        if req.hook:
            if inspect.iscoroutinefunction(req.hook):
                hook_result = await req.hook(headers=req.headers, body=req.body)
            else:
                hook_result = req.hook(headers=req.headers, body=req.body)
                if inspect.isawaitable(hook_result):
                    hook_result = await hook_result

            if isinstance(hook_result, tuple):
                body_obj, extra_headers, status = hook_result
                response = self._build_json_response(body_obj, status=status, extra_headers=extra_headers, origin=origin)
            else:
                response = self._build_json_response(hook_result, origin=origin)
        else:
            response = resp.build_response(req)

        writer.write(response)
        await writer.drain()

    @property
    def extract_cookies(self, req, resp):
        """Legacy helper kept for compatibility."""
        return {}

    def build_response(self, req, resp):
        """Legacy helper kept for compatibility."""
        return Response(req)

    def build_json_response(self, req, resp):
        """Legacy helper kept for compatibility."""
        return Response(req)


    # def get_connection(self, url, proxies=None):
        # """Returns a url connection for the given URL. 

        # :param url: The URL to connect to.
        # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
        # :rtype: int
        # """

        # proxy = select_proxy(url, proxies)

        # if proxy:
            # proxy = prepend_scheme_if_needed(proxy, "http")
            # proxy_url = parse_url(proxy)
            # if not proxy_url.host:
                # raise InvalidProxyURL(
                    # "Please check proxy URL. It is malformed "
                    # "and could be missing the host."
                # )
            # proxy_manager = self.proxy_manager_for(proxy)
            # conn = proxy_manager.connection_from_url(url)
        # else:
            # # Only scheme should be lower case
            # parsed = urlparse(url)
            # url = parsed.geturl()
            # conn = self.poolmanager.connection_from_url(url)

        # return conn


    def add_headers(self, request):
        """
        Add headers to the request.

        This method is intended to be overridden by subclasses to inject
        custom headers. It does nothing by default.

        
        :param request: :class:`Request <Request>` to add headers to.
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 

        :class:`HttpAdapter <HttpAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        headers = {}
        username, password = ("user1", "password")

        if username:
            headers["Proxy-Authorization"] = (username, password)

        return headers