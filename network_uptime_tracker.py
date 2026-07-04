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

# Removes null hosts
df = df.dropna(subset=["host"])

# Makes the timestamps be at the nearest minute
df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.floor("min")

# Creates the first metric
with metric_1:
    if not df.empty:
        # 1. Get the latest timestamp
        current_run = df["timestamp"].max()

        # 2. Get the unique hosts for the current run
        current_count = df[df["timestamp"] <= current_run]["host"].nunique()

        # 3. Filter for older data to find the *true* previous timestamp
        past_runs = df[df["timestamp"] < current_run]

        if not past_runs.empty:
            prev_run = past_runs["timestamp"].max()
            prev_count = df[df["timestamp"] <= prev_run]["host"].nunique() if not past_runs.empty else None
            delta_val = int(current_count - prev_count)
        else:
            delta_val = None

        # 4. Render the metric
        st.metric(label="Total hosts", value=current_count, delta=delta_val)
    else:
        st.metric(label="Total hosts", value=0, delta=None)

# Creates the total online metric
with metric_2:
    # 1. Get the latest timestamp
    current_run = df["timestamp"].max()
    
    # 2. Get all rows that belong to older runs
    past_runs = df[df["timestamp"] < current_run]

    # 3. Calculate current online hosts
    current_count = df[(df["timestamp"] == current_run) & (df["online"] == 1)]["host"].nunique()

    # 4. Calculate previous online hosts safely
    if not past_runs.empty:
        prev_run = past_runs["timestamp"].max()
        prev_count = df[(df["timestamp"] == prev_run) & (df["online"] == 1)]["host"].nunique()
        delta_val = int(current_count - prev_count)
    else:
        delta_val = None

    # 5. Display the metric
    st.metric(
        label="Total hosts online", 
        value=current_count, 
        delta=delta_val
    )

# Creates the total offline metric
with metric_3:
    # 1. Get the latest timestamp
    current_run = df["timestamp"].max()
    
    # 2. Get all rows that belong to older runs
    past_runs = df[df["timestamp"] < current_run]

    # 3. Calculate current OFFLINE hosts (online == False)
    current_count = df[(df["timestamp"] == current_run) & (df["online"] == 0)]["host"].nunique()

    # 4. Calculate previous OFFLINE hosts safely
    if not past_runs.empty:
        prev_run = past_runs["timestamp"].max()
        prev_count = df[(df["timestamp"] == prev_run) & (df["online"] == 0)]["host"].nunique()
        delta_val = int(current_count - prev_count)
    else:
        delta_val = None

    # 5. Display the metric
    st.metric(
        label="Total hosts offline", 
        value=current_count, 
        delta=delta_val
    )

# Fourth metric for average response
with metric_4:
    # 1. Get the latest timestamp
    current_run = df["timestamp"].max()
    
    # 2. Get all rows that belong to older runs
    past_runs = df[df["timestamp"] < current_run]

    # 3. Calculate current average response time
    current_average = df[df["timestamp"] == current_run]["response_time_ms"].mean()

    # 4. Calculate previous average safely
    if not past_runs.empty:
        prev_run = past_runs["timestamp"].max()
        prev_average = df[df["timestamp"] == prev_run]["response_time_ms"].mean()
        
        # Check if both values are valid numbers before calculating delta
        if pd.notna(current_average) and pd.notna(prev_average):
            delta_val = f"{current_average - prev_average:+.2f} ms"
        else:
            delta_val = None
    else:
        delta_val = None

    # 5. Format current display value (handles empty data gracefully)
    display_value = f"{current_average:.2f} ms" if pd.notna(current_average) else "N/A"

    # 6. Display the metric
    st.metric(
        label="Average Response Time", 
        value=display_value, 
        delta=delta_val,
        delta_color="inverse" # Optional: Turns a positive delta (higher latency) RED instead of GREEN
    )

# Creates column to store line chart
with col_1:
    st.subheader("Online Hosts Over Time")
    
    # .sum() adds up all the 1s, giving you the true online count per timestamp
    grouped_by_date = (
        df.groupby("timestamp")["online"]
        .sum()
        .reset_index(name="Online Hosts")
    )
    
    # Explicitly set x and y for a clean, well-labeled chart
    st.line_chart(
        data=grouped_by_date, 
        x="timestamp", 
        y="Online Hosts"
    )

# Column to store the data frame
with col_2:
    st.subheader("Recent Ingestion Data")
    
    # Sorts the data by timestamp so the latest logs are right at the top
    sorted_data = df.sort_values("timestamp", ascending=False)

    # Displays the data frame using full container width
    st.dataframe(sorted_data, use_container_width=True)

# Auto-refresh every 10 seconds
time.sleep(10)
st.rerun()