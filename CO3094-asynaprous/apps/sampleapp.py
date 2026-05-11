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

from   daemon import AsynapRous

app = AsynapRous()

@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    print("[SampleApp] Logging in {} to {}".format(headers, body))
    data = {"message": "Welcome to the RESTful TCP WebApp"}

    # Convert to JSON string
    json_str = json.dumps(data)
    return (json_str.encode("utf-8"))

@app.route("/echo", methods=["POST"])
def echo(headers="guest", body="anonymous"):
    print("[SampleApp] received body {}".format(body))

    try:
        message = json.loads(body)
        data = {"received": message }
        # Convert to JSON string
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"))
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON"}
        # Convert to JSON string
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"))


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

# --- P2P Chat Application Endpoints ---
active_peers = []
chat_messages = []

@app.route('/submit-info', methods=['POST'])
def submit_info(headers, body):
    try:
        peer_info = json.loads(body)
        if peer_info not in active_peers:
            active_peers.append(peer_info)
        return json.dumps({"status": "success", "active_peers": active_peers}).encode("utf-8")
    except:
        return json.dumps({"error": "Invalid payload"}).encode("utf-8")

@app.route('/get-list', methods=['GET'])
def get_list(headers, body):
    return json.dumps({"active_peers": active_peers}).encode("utf-8")

@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(headers, body):
    try:
        msg_info = json.loads(body)
        chat_messages.append(msg_info)
        return json.dumps({"status": "broadcasted", "messages": chat_messages}).encode("utf-8")
    except:
        return json.dumps({"error": "Invalid payload"}).encode("utf-8")

@app.route('/send-peer', methods=['POST'])
def send_peer(headers, body):
    # Logic for direct P2P messaging
    return json.dumps({"status": "message_sent"}).encode("utf-8")
    app.prepare_address(ip, port)
    app.run()

