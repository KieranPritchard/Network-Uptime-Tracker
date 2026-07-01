import time
import streamlit as st
import pandas as pd
import sqlite3
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
        # FIX: strip() removes trailing newlines/whitespace that would break
        # the regex match and hostname resolution
        locations = [line.strip() for line in f.readlines()]

    # Stores the resolved locations
    resolved = []

    # Loops over each of the locations
    for location in locations:
        # Skips a blank line
        if not location:
            continue

        # Checks if the location is already a valid location
        if IPV4_PATTERN.match(location):
            # Adds the pattern to the resolved
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

        # Starts the response timer
        start = time.perf_counter()

        # Stores the response from the location
        response = sr1(packet, timeout=1, verbose=0)

        # Stores the elapsed time
        elapsed = (time.perf_counter() - start) * 1000

        # FIX: inverted online/offline logic and inconsistent key names corrected
        if response is None:
            results.append({"host": ip, "online": False, "response_time_ms": 0, "timestamp": datetime.now()})
            print(f"  {ip:20s}  OFFLINE")
        else:
            rtt = round(elapsed, 2)
            results.append({"host": ip, "online": True, "response_time_ms": rtt, "timestamp": datetime.now()})
            print(f"  {ip:20s}  ONLINE   {rtt} ms")

    # Returns the results
    return results

def store_results_in_sql(results: list[dict]):
    """Function to store results in sqlite database"""

    # Creates a data frame with the results
    df = pd.DataFrame(results)

    # Checks if the results file exists
    if not os.path.exists("./results.db"):
        # Creates the file to store the data long term
        file = open("./results.db", "w")

        # Closes the file
        file.close()

    # Connects to the SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect("./results.db")

    # Saves the dataframe to the database
    df.to_sql("results", conn, if_exists="append", index=False)

    # Closes the connection
    conn.close()

def load_history_from_sql() -> pd.DataFrame:
    """Loads all historical results from the SQLite database"""

    if not os.path.exists("./results.db"):
        return pd.DataFrame()

    conn = sqlite3.connect("./results.db")
    df = pd.read_sql("SELECT * FROM results", conn)
    conn.close()

    return df

# Sets the page configuration
st.set_page_config(page_title="Server Status Dashboard", layout="wide")

# Gives the page a title
st.title("Network Uptime Tracker")

# Creates four columns for the metrics
metric_1, metric_2, metric_3, metric_4 = st.columns(4)

# Creates a wide and a narrow column for the chart and dataframe
col_1, col_2 = st.columns([3, 2])

# Gets all of the server locations
resolved = get_all_server_locations("./hosts.txt")

# Stores the results of the ping sweep
results = ping_sweep(resolved)

# Stores the results to sql
store_results_in_sql(results)

# Gets the data from the sql shit
df = load_history_from_sql()

# Creates the first metric
with metric_1:
    # Store the current runs timestamp
    current_run = df["timestamp"].max()

    # Stores the previous runs timestamp
    prev_run = df[df["timestamp"] != current_run]["timestamp"].max()

    # Stores the current count for the time stamp
    current_count = df[df["timestamp"] == current_run]["host"].nunique()
    
    # Stores the previous run
    prev_count = df[df["timestamp"] == prev_run]["host"].nunique() if prev_run else None

    # Displays the metric
    st.metric("Total hosts", current_count, delta=current_count - prev_count if prev_count is not None else None)

# Creates the total online metric
with metric_2:
    # Stores the current runs time stamp
    current_run = df["timestamp"].max()
    
    # Stores the previous runs timestamp
    prev_run = df[df["timestamp"] != current_run]["timestamp"].max()

    # Stores the current count for the time stamp
    current_count = df[df["timestamp"] == current_run]["online"].count()

    # Stores the count from the previous run
    prev_count = df[df["timestamp"] == prev_run]["online"].nunique() if prev_run else None

    # Displays the metric
    st.metric("Total hosts online", current_count, delta=current_count - prev_count if prev_count is not None else None)

# Creates the total offline metric
with metric_3:
    # Stores the current runs time stamp
    current_run = df["timestamp"].max()
    
    # Stores the previous runs timestamp
    prev_run = df[df["timestamp"] != current_run]["timestamp"].max()

    # Stores the current count of hosts
    current_host_count = df[df["timestamp"] == current_run]["host"].nunique()

    # Stores the previous host count
    prev_host_count = df[df["timestamp"] == prev_run]["online"].nunique() if prev_run else None

    # Stores the current count for the time stamp
    current_count_online = df[df["timestamp"] == current_run]["online"].count()

    # Stores the count from the previous run
    prev_count_online = df[df["timestamp"] == prev_run]["online"].nunique() if prev_run else None

    # Stores the current count
    current_count = current_host_count - current_count_online

    # Stores the previous count
    prev_count = prev_host_count - prev_count_online

    # Displays the metric
    st.metric("Total hosts offline", current_count, delta=current_count - prev_count if prev_count is not None else None)

# Fourth metric for average response
with metric_4:
    # Stores the current run
    current_run = df["timestamp"].max()

    # Stores the previous runs timestamp
    prev_run = df[df["timestamp"] != current_run]["timestamp"].max()

    # Gets the current average
    current_average = df[df["timestamp"] == current_run]["response_time_ms"].mean()

    # Gets the previous average
    prev_average = df[df["timestamp"] == prev_run]["response_time_ms"].mean()

    # Displays the metric
    st.metric("Average Response Time", current_average, delta=current_average - prev_average if prev_average is not None else None)

# Creates column to store line chart
with col_1:
    # Groups the data by date
    grouped_by_date = df.groupby("timestamp")["online"].count()

    # Displays a line graph
    st.line_chart(grouped_by_date)

# Column to store the data frame
with col_2:
    # Sorts the data by timestamp
    sorted_data = df.sort_values("timestamp", ascending=False)

    # Displays the data frame
    st.dataframe(sorted_data)

# Auto-refresh every 10 seconds
time.sleep(10)
st.rerun()