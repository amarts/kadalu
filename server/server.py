#!/usr/bin/python3

"""
Prepares, Validates and then starts the Server process(glusterfsd, shd)
"""

import os
from prometheus_client import start_http_server

from kadalulib import logging_setup, KADALU_PROMETHEUS_PORT
import glusterfsd
import shd
import quotad


def start_server_process():
    """
    Start glusterfsd or glustershd process
    """
    server_role = os.environ.get("KADALU_SERVER_ROLE", "glusterfsd")
    if server_role == "glusterfsd":
        start_http_server(KADALU_PROMETHEUS_PORT)
        glusterfsd.start()
    elif server_role == "shd":
        start_http_server(KADALU_PROMETHEUS_PORT + 1)
        shd.start()
    elif server_role == "quotad":
        # Add an exporter when there are metrics to send out.
        # Right now, nothing
        quotad.start()

    pass

if __name__ == "__main__":
    logging_setup()
    start_server_process()
