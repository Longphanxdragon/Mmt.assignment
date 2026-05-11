#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
app.sampleapp
~~~~~~~~~~~~~~~~~

"""

import sys
import os
import importlib.util
import json
import base64
import secrets
import asyncio
import urllib.request
import urllib.error

from   daemon import AsynapRous

app = AsynapRous()

active_peers = []
chat_messages = []
sessions = {}


def _json_tuple(payload, status=200, extra_headers=None):
    return (payload, extra_headers or {}, status)

async def send_to_peer(peer_ip, peer_port, endpoint, message_data):
    """
    Send message to a peer asynchronously using HTTP POST.
    This implements actual P2P messaging instead of just storing locally.
    
    :param peer_ip: IP address of target peer
    :param peer_port: Port of target peer
    :param endpoint: API endpoint (/receive-message)
    :param message_data: Message payload (dict)
    """
    try:
        url = f"http://{peer_ip}:{peer_port}{endpoint}"
        json_data = json.dumps(message_data).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        loop = asyncio.get_event_loop()
        # Run blocking operation in thread pool
        def _send():
            try:
                response = urllib.request.urlopen(req, timeout=5)
                return response.read().decode('utf-8')
            except urllib.error.URLError as e:
                print(f"[P2P] Failed to send to {peer_ip}:{peer_port} - {e}")
                return None
        
        result = await loop.run_in_executor(None, _send)
        if result:
            print(f"[P2P] Message sent to {peer_ip}:{peer_port}: {result[:50]}...")
    except Exception as e:
        print(f"[P2P] Error sending message to {peer_ip}:{peer_port}: {e}")

@app.route('/receive-message', methods=['POST'])
def receive_message(headers=None, body=""):
    """
    Endpoint for peers to receive direct messages (P2P).
    """
    try:
        msg_info = json.loads(body)
        chat_messages.append(msg_info)
        print(f"[P2P] Received message from peer: {msg_info}")
        return _json_tuple({
            "status": "received",
            "message_id": len(chat_messages),
            "total_messages": len(chat_messages)
        })
    except Exception as e:
        return _json_tuple({"error": str(e)}, 400)

@app.route('/login', methods=['POST'])
def login(headers=None, body=""):
    """Authenticate a demo user with Basic auth or JSON credentials."""
    print("[SampleApp] Login attempt headers={} body={}".format(headers, body))

    auth = headers.get('authorization') if headers else None
    valid = False

    if auth and auth.lower().startswith('basic '):
        try:
            token = auth.split(None, 1)[1].strip()
            decoded = base64.b64decode(token).decode('utf-8')
            user, pwd = decoded.split(':', 1)
            valid = user == 'student' and pwd == 'pass123'
        except Exception:
            valid = False

    if not valid and body:
        try:
            data = json.loads(body)
            valid = data.get('user') == 'student' and data.get('pass') == 'pass123'
        except Exception:
            valid = False

    if not valid:
        return _json_tuple(
            {"error": "unauthorized"},
            401,
            {"WWW-Authenticate": 'Basic realm="AsynapRous"'}
        )

    session_id = secrets.token_hex(16)
    sessions[session_id] = {"user": "student"}
    return _json_tuple(
        {"message": "login ok", "session": session_id},
        200,
        {"Set-Cookie": f"sessionid={session_id}; Path=/; HttpOnly"}
    )


@app.route('/whoami', methods=['GET'])
def whoami(headers=None, body=""):
    cookie_header = headers.get('cookie') if headers else None
    session_id = None

    if cookie_header:
        for item in cookie_header.split(';'):
            key, _, value = item.strip().partition('=')
            if key == 'sessionid':
                session_id = value
                break

    if session_id in sessions:
        return _json_tuple({"authenticated": True, "session": session_id, "user": sessions[session_id]["user"]})

    return _json_tuple({"authenticated": False}, 401)

@app.route("/echo", methods=["POST"])
def echo(headers="guest", body="anonymous"):
    print("[SampleApp] received body {}".format(body))

    try:
        message = json.loads(body)
        return _json_tuple({"received": message})
    except json.JSONDecodeError:
        return _json_tuple({"error": "Invalid JSON"}, 400)


@app.route('/hello', methods=['PUT'])
async def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] **ASYNC** Hello in {} to {}".format(headers, body))
    data =  {"id": 1, "name": "Alice", "email": "alice@example.com"}

    # Convert to JSON string
    json_str = json.dumps(data)
    return (json_str.encode("utf-8"))

def create_sampleapp(ip, port):
    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()

@app.route('/submit-info', methods=['POST'])
def submit_info(headers, body):
    try:
        peer_info = json.loads(body)
        peer_id = peer_info.get('peer_id')
        if not peer_id:
            return _json_tuple({"error": "peer_id is required"}, 400)

        normalized = {
            "peer_id": peer_id,
            "ip": peer_info.get('ip', '127.0.0.1'),
            "port": peer_info.get('port'),
        }

        replaced = False
        for index, existing in enumerate(active_peers):
            if existing.get('peer_id') == peer_id:
                active_peers[index] = normalized
                replaced = True
                break

        if not replaced:
            active_peers.append(normalized)

        return _json_tuple({"status": "success", "active_peers": active_peers})
    except Exception:
        return _json_tuple({"error": "Invalid payload"}, 400)

@app.route('/get-list', methods=['GET'])
def get_list(headers, body):
    return _json_tuple({"active_peers": active_peers})


@app.route('/add-list', methods=['POST'])
def add_list(headers, body):
    return submit_info(headers, body)


@app.route('/connect-peer', methods=['POST'])
def connect_peer(headers, body):
    try:
        payload = json.loads(body)
        peer_id = payload.get('peer_id')
        target = next((peer for peer in active_peers if peer.get('peer_id') == peer_id), None)
        if not target:
            return _json_tuple({"error": "peer not found"}, 404)

        return _json_tuple({"status": "ready", "peer": target})
    except Exception:
        return _json_tuple({"error": "Invalid payload"}, 400)

@app.route('/broadcast-peer', methods=['POST'])
async def broadcast_peer(headers, body):
    """
    Broadcast message to all active peers (P2P messaging).
    Sends HTTP POST requests to each peer's /receive-message endpoint.
    """
    try:
        msg_info = json.loads(body)
        sender = msg_info.get('sender', 'anonymous')
        content = msg_info.get('content', '')
        
        # Store locally
        message_record = {
            "sender": sender,
            "content": content,
            "type": "broadcast",
            "timestamp": len(chat_messages)
        }
        chat_messages.append(message_record)
        
        print(f"[P2P] Broadcasting from {sender}: {content}")
        
        # Send to all active peers asynchronously
        tasks = []
        for peer in active_peers:
            if peer.get('ip') and peer.get('port'):
                task = send_to_peer(
                    peer['ip'], 
                    peer['port'],
                    '/receive-message',
                    message_record
                )
                tasks.append(task)
        
        # Execute all sends concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return _json_tuple({
            "status": "broadcasted",
            "peers_notified": len(active_peers),
            "message": message_record,
            "messages": chat_messages
        })
    except Exception as e:
        return _json_tuple({"error": str(e)}, 400)

@app.route('/send-peer', methods=['POST'])
async def send_peer(headers, body):
    """
    Send direct message to a specific peer (P2P messaging).
    Sends HTTP POST request to target peer's /receive-message endpoint.
    """
    try:
        msg_info = json.loads(body)
        sender = msg_info.get('sender', 'anonymous')
        target_peer_id = msg_info.get('target_peer_id')
        content = msg_info.get('content', '')
        
        # Find target peer
        target_peer = next(
            (p for p in active_peers if p.get('peer_id') == target_peer_id),
            None
        )
        
        if not target_peer:
            return _json_tuple({"error": "target peer not found"}, 404)
        
        # Store locally
        message_record = {
            "sender": sender,
            "target_peer_id": target_peer_id,
            "content": content,
            "type": "direct",
            "timestamp": len(chat_messages)
        }
        chat_messages.append(message_record)
        
        print(f"[P2P] Direct message from {sender} to {target_peer_id}: {content}")
        
        # Send to target peer
        if target_peer.get('ip') and target_peer.get('port'):
            await send_to_peer(
                target_peer['ip'],
                target_peer['port'],
                '/receive-message',
                message_record
            )
        
        return _json_tuple({
            "status": "message_sent",
            "target": target_peer_id,
            "message": message_record
        })
    except Exception as e:
        return _json_tuple({"error": str(e)}, 400)

