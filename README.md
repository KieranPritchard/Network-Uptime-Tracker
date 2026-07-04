# Network Uptime Tracker

![GitHub Created At](https://img.shields.io/github/created-at/KieranPritchard/Network-Uptime-Tracker) ![GitHub License](https://img.shields.io/github/license/KieranPritchard/Network-Uptime-Tracker) ![GitHub commit activity](https://img.shields.io/github/commit-activity/t/KieranPritchard/Network-Uptime-Tracker) ![GitHub last commit](https://img.shields.io/github/last-commit/KieranPritchard/Network-Uptime-Tracker) ![GitHub language count](https://img.shields.io/github/languages/count/KieranPritchard/Network-Uptime-Tracker) ![GitHub Repo stars](https://img.shields.io/github/stars/KieranPritchard/Network-Uptime-Tracker)

## Project Description

### Objective

To build a live network monitoring dashboard that pings a list of hosts, logs the results long term, and displays uptime and response times in a way that's actually readable, instead of just printing text to a terminal.

### Features

- Host Resolution: Reads targets from `hosts.txt`, validates raw IPv4 addresses with a regex, and resolves anything else as a hostname via `socket.gethostbyname()`, skipping entries that can't be resolved.
- ICMP Ping Sweep: Uses Scapy to build and send ICMP echo packets to every resolved host, timing the response to get a round trip time and marking each host online or offline.
- Persistent History: Appends every sweep's results to a local SQLite database (`results.db`) through pandas, so the dashboard builds up a real history across runs instead of just showing the latest check.
- Live Dashboard: A Streamlit front end showing four live metrics (total hosts, hosts online, hosts offline, average response time), each with a delta against the previous run, alongside a line chart of hosts online over time and a sortable table of the full history.
- Auto-Refresh: The whole sweep reruns and the dashboard refreshes automatically every 10 seconds.

### Technology and Tools Used

- **Language:** Python.
- **Framework/Library:** Streamlit, Pandas, Scapy, sqlite3.
- **Tools:** Git, VS Code.

### Challenges Faced

I had an issue where hostname resolution kept failing on entries that should have worked fine. It turned out `readlines()` was leaving trailing newlines on each line from `hosts.txt`, which broke both the IPv4 regex match and `socket.gethostbyname()`. Fixed it by stripping each line before doing anything else with it.

I also had the online/offline logic inverted at one point, alongside inconsistent key names in the results dictionaries, which meant the "online" and "offline" counts on the dashboard didn't line up with what was actually happening on the network. Went through the `ping_sweep()` function properly and corrected both the logic and the key names so the rest of the pipeline (SQL storage, metrics, chart) could rely on them.

### Outcome

The project successfully pings a list of hosts, stores the results persistently, and displays them as a live-updating dashboard with metrics, a trend chart, and a full history table. It gave me hands-on experience with Scapy for raw ICMP packets, pandas for moving data in and out of SQLite, and Streamlit for building a dashboard that actually updates itself rather than needing a manual refresh.

## How to Use the Project

1. **Clone the Repository:**
   - Use git to clone the project.

2. **Install Dependencies:**
   - Make sure Python is installed, then install the required libraries:

   ```
   pip install streamlit pandas scapy
   ```

3. **Set Up Your Host List:**
   - Open `hosts.txt` and add one IP address or hostname per line.
   - Blank lines are skipped, and anything that can't be resolved will show a warning on the dashboard rather than crashing the app.

4. **Run the Dashboard:**
   - Scapy needs to send raw ICMP packets, so on Linux/macOS run it with elevated privileges, and on Windows make sure Npcap is installed:

   ```
   sudo streamlit run network_uptime_tracker.py
   ```

5. **Read the Dashboard:**
   - The four metrics at the top show total hosts, hosts online, hosts offline, and average response time, each with the change since the last sweep.
   - The line chart tracks hosts online over time, and the table on the right shows the full sweep history, most recent first.
   - The page refreshes itself every 10 seconds, so just leave it open.

## Licenses

License is located in the root of the repository.
