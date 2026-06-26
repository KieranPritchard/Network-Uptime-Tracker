import time
import streamlit as st
from scapy.all import IP, ICMP, sr1
from datetime import datetime
import socket
import os
import re

# Stores the ipv4 pattern
IPV4_PATTERN = re.compile(
    r'^((25[0-5]|2[0-4]\d|1\d{2}|[1-9]\d|\d)\.){3}'
    r'(25[0-5]|2[0-4]\d|1\d{2}|[1-9]\d|\d)$'
)

def get_all_server_locations(filepath: str) -> list:
    """Function to get all of the server locations from a file"""

    # Checks if the filepath was passed into the function
    if not filepath:
        # Outputs an error to the screen
        st.error("A file path must be specified")

    # Checks if the file path exists
    if not os.path.exists(filepath):
        # Outputs an error to the screen
        st.error("A file path does not exist")

    # Checks if the file is a txt file
    if not filepath.endswith(".txt"):
        # Outputs an error to the screen
        st.error("The file must be a .txt")

    # Opens the file
    with open(filepath) as f:
        # Reads the file and saves the location to a variable
        locations = f.readlines()

    # Stores the resolved locations
    resolved = []

    # Loops over each of the locations
    for location in locations:
        # Skips a blank line
        if not location:
            continue

        # Checks if the location is already a valid location
        if IPV4_PATTERN.match(location):
            # Adds the pattern to the reolved
            resolved.append(location)
        else:
            # Treat it as a hostname and attempt to resolve it to an IP
            try:
                # gets the ip address from the host name
                ip = socket.gethostbyname(location)
                # Adds it to the resolved page
                resolved.append(ip)
            except socket.gaierror:
                # Displays a warning message
                st.warning(f"Could not resolve '{location}' — skipping")

    # Returns the locations variable
    return resolved

def ping_sweep(resolved: list[str]) -> list:
    """Function to ping the resolved location and gather data about it"""

    # Stores results
    results = []

    # Loops over the hosts in resolved
    for host in resolved:
        
        # Stores the ip address
        ip = str(host)

        # Creates an echo packet
        packet = IP(dst=host) / ICMP()

        # Sarts the response timer
        start = time.perf_counter()

        # Stores the response from the location
        response = sr1(packet, timeout=1, verbose=0)

        # Stores the elasped time
        elapsed = (time.perf_counter() - start) * 1000

        # Checks if there is a response
        if response is None:
            results.append({"host": ip, "online": True, "response_time_ms": 0, "timestamp": datetime.now()})
            print(f"  {ip:20s}  OFFLINE")
        else:
            rtt = round(elapsed, 2)
            results.append({"host": ip, "status": False, "response_time_ms": rtt, "timestamp": datetime.now()})
            print(f"  {ip:20s}  ONLINE   {rtt} ms")

    # Returns the results
    return results

# Sets the page configuration
st.set_page_config(page_title="Server Status Dashboard", layout="wide")