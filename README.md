# Huawei ONT Monitoring Stack

This project provides a complete, containerized monitoring solution for Huawei Optical Network Terminals (ONTs) using Prometheus and Grafana. It automatically collects various statistics from the device via SSH, parses the data, and visualizes it in real-time dashboards.

## Overview

The system is composed of several services managed by Docker Compose:
1.  **Collector:** A Python script that periodically connects to the ONT via SSH, runs a series of commands, and parses the raw output.
2.  **Exporter:** A lightweight Python web server that reads the parsed data and exposes it as Prometheus-compatible metrics.
3.  **Prometheus:** A leading time-series database that scrapes the metrics from the exporter and stores them.
4.  **Grafana:** A powerful visualization platform used to create dashboards from the data stored in Prometheus.

## Features

* **Automated Data Collection:** Runs commands at configurable intervals.
* **Comprehensive Parsing:** Includes specialized parsers for various command outputs.
* **Persistent Storage:** Both Prometheus metrics and Grafana dashboards are stored in Docker volumes.
* **Fully Containerized:** The entire stack is managed by Docker Compose for easy setup.
* **Integrated Data Cleanup:** The collector script automatically cleans up old data files.
* **Secure Configuration:** Uses a `.env` file to manage secrets and paths.
* **Automatic Provisioning:** The Prometheus data source and a default dashboard are automatically provisioned in Grafana on first startup.

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


## Compatibility

*Note:* This project has been developed and tested specifically with a Huawei OptiXstar HG8145X6-10 ONT. While the parsers may work for other Huawei models, compatibility is not guaranteed.

## Prerequisites

* [Docker](https://www.docker.com/get-started) & [Docker Compose](https://docs.docker.com/compose/install/)
* Git
* **SSH access to the target ONT device.** The device must be reachable from the machine running the Docker stack.

> [!NOTE] 
>Enabling SSH Access on the Huawei `HG8145X6-10 ONT`:
>- Log into the web interface (e.g., `192.168.100.1`).
>- Navigate to Advanced Settings > Security > Precise Device Access Control.
>- Enable Precise Device Access Control if it's disabled.
>- Click New and configure the rule:
>      - Port Type: `LAN`
>      - Port Name: Select the port you will connect from
>      - Appliacation: `SSH` (You can select other ones if desired)
>      - SSH Password: Create your SSH password and confirm it below
>      - Mode: `Permit`
>      - Click `Apply` to save.

## Setup & Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/andreiciupac/huawei-ont-monitoring.git](https://github.com/andreiciupac/huawei-ont-monitoring.git)
    cd huawei-ont-monitoring
    ```

2.  **Create Configuration File**
    Copy the example environment file to create your own local configuration.
    ```bash
    cp .env.example .env
    ```

> [!NOTE] 
>Make sure that the ~/.ssh/config file exists and is configured
>It should look something like this:
>  ```
>  Host ont
>    Hostname 192.168.100.1
>    User root
>  ```

3.  **Configure `.env`**
    Open the newly created `.env` file and fill in your specific details:
    * `SSH_HOST_ALIAS`: Must match the `Host` name in your `~/.ssh/config` file.
    * `ONT_PASSWORD`: Your SSH password.
    * `CLEANUP_OLDER_THAN`: Set your desired data retention (e.g., `7d`, `48h`, `15m`).
    * `CLEANUP_FREQUENCY`: Set how often the cleanup job runs (e.g., `1d`, `1h`, `30m`).

4.  **Build and Start the Stack**
    Run the following command from the root of the project directory.
    ```bash
    docker-compose up -d --build
    ```

## Usage

* **Start the services:** `docker-compose up -d`
* **Stop the services:** `docker-compose down`
* **View logs for a specific service:** `docker-compose logs -f <service_name>` (e.g., `collector`, `exporter`)

### Accessing the Services

Once the stack is running, you can access the frontends in your web browser:
* **Prometheus:** `http://localhost:9090`
* **Grafana:** `http://localhost:3000` (Default login: `admin` / `admin`)

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
