# Huawei ONT Monitoring Stack

This project provides a complete, containerized monitoring solution for Huawei Optical Network Terminals (ONTs) using Prometheus and Grafana. It automatically collects various statistics from the device via SSH, parses the data, and visualizes it in real-time dashboards.

## Overview

The system is composed of several services managed by Docker Compose:

1. Collector: A Python script that periodically connects to the ONT via SSH, runs a series of commands, and parses the raw output.

2. Exporter: A lightweight Python web server that reads the parsed data and exposes it as Prometheus-compatible metrics.

3. Prometheus: A leading time-series database that scrapes the metrics from the exporter and stores them.

4. Grafana: A powerful visualization platform used to create dashboards from the data stored in Prometheus.

## Features

- Automated Data Collection: Runs commands at configurable intervals (e.g., every 1 and 5 minutes) using a built-in scheduler.

- Comprehensive Parsing: Includes specialized parsers for various command outputs, from simple key-value pairs to complex tables.

- Persistent Storage: Both Prometheus metrics and Grafana dashboards are stored in Docker volumes, ensuring data survives restarts.

- Fully Containerized: The entire stack, including the custom Python scripts, is managed by Docker Compose for easy setup and deployment.

- Log Rotation: Includes a cron job to automatically clean up old data files, preventing disk space from filling up.

- Extensible: The modular structure makes it easy to add new commands and parsers.

## Architecture

```
+----------------+      +------------------+      +-------------------+      +-----------+
| Huawei ONT     | <--- | Collector        | ---> | /clean_data       | ---> | Exporter  |
| (SSH Server)   |      | (Python script   |      | (Shared Volume)   |      | (Python   |
+----------------+      | in Docker)       |      +-------------------+      | in Docker)|
                        +------------------+                                 +-----------+
                                                                                   |
                                                                                   | (Scrapes /metrics)
                                                                                   v
                                                                             +-------------+
                                                                             | Prometheus  |
                                                                             | (in Docker) |
                                                                             +-------------+
                                                                                   |
                                                                                   | (Queries data)
                                                                                   v
                                                                             +-----------+
                                                                             | Grafana   |
                                                                             |(in Docker)|
                                                                             +-----------+
```


### Compatibility

*Note:* This project has been developed and tested specifically with a Huawei OptiXstar HG8145X6-10 ONT. While the parsers may work for other Huawei models, compatibility is not guaranteed.

## Prerequisites

- Docker & Docker Compose

- Python 3.x (for running the setup)

- Git

- *SSH access to the target ONT device.* The device must be reachable from the machine running the Docker stack.

- A configured `~/.ssh/config` file with an entry for your ONT device.

## Setup & Installation

1. Clone the Repository

```bash
git clone https://github.com/andreiciupac/huawei-ont-monitoring.git
cd huawei-ont-monitoring
```

2. Configure SSH
Ensure your `~/.ssh/config` file contains an entry for your router, for example:

```
Host ont.home
    HostName 192.168.100.1
    User your_ssh_username
    Port 22
```

The collector container will mount and use this file to resolve the hostname.

3. Configure the Collector
Open `collector/config.py` and edit the following variables:

- `SSH_HOST_ALIAS`: Must match the Host name in your ~/.ssh/config file.

- `PASSWORD`: Your SSH password.

- `CLEAN_DATA_DIR`: This should remain as '/data', as it refers to the path inside the container.

4. Build and Start the Stack
Run the following command from the root of the project directory. This will build the custom Docker images for the collector and exporter, and start all services in the background.

```bash
docker-compose up -d --build
```

## Usage

- Start the services: `docker-compose up -d`

- Stop the services: `docker-compose down`

- View logs for a specific service: `docker-compose logs -f <service_name>` (e.g., collector, exporter)

### Accessing the Services

Once the stack is running, you can access the frontends in your web browser:

- Prometheus: `http://localhost:9090`

- Grafana: `http://localhost:3000` (Default login: admin / admin)

### First-Time Grafana Setup

1. Log in to Grafana.

2. Navigate to Configuration (cogwheel) > Data Sources.

3. Click Add data source and select Prometheus.

4. Set the Prometheus server URL to http://prometheus:9090.

5. Click Save & test. You should see a success message.

6. You can now create dashboards using the metrics collected from your device!

## Folder Structure

```
monitoring_stack/
├── collector/          # Contains all scripts for gathering and parsing data.
│   ├── main.py         # The main entry point that starts the scheduler.
│   ├── config.py       # Central configuration for command lists and settings.
│   ├── ssh_manager.py  # Handles the SSH connection logic.
│   ├── parsers.py      # Contains all specialized functions to parse command outputs.
│   ├── scheduler.py    # Contains the logic for scheduling jobs.
│   ├── Dockerfile      # Recipe for building the collector's Docker image.
│   └── requirements.txt# Python libraries needed for the collector.
│
├── exporter/           # Contains the script to expose metrics to Prometheus.
│   ├── exporter.py     # The Python script that runs a web server for Prometheus to scrape.
│   ├── Dockerfile      # Recipe for building the exporter's Docker image.
│   └── requirements.txt# Python libraries needed for the exporter.
│
├── grafana/            # Contains all assets for automatically setting up Grafana.
│   ├── dashboards/
│   │   └── ont_dashboard.json # Your pre-built dashboard file goes here.
│   └── provisioning/
│       └── dashboards/
│           └── main.yml  # Tells Grafana to load dashboards from the above folder.
│
├── .env                  # Your private file for secrets (passwords, paths). Ignored by Git.
├── .env.example          # An example file showing users what variables to set in .env.
├── .gitignore            # Specifies which files and folders Git should ignore.
├── docker-compose.yml    # The main file that defines and orchestrates all Docker services.
├── prometheus.yml        # Configuration file for Prometheus, telling it what to scrape.
└── README.md             # The main documentation for the project.
```
