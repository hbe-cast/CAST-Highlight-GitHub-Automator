# CAST Highlight GitHub Automator Setup Guide

This guide outlines the steps to set up and run the CAST Highlight GitHub Automator, which automates repository cloning and scans in response to push events.

## Application Overview

1. **[CAST Highlight GitHub Automator](https://github.com/hbe-cast/CAST-Highlight-GitHub-Automator/releases)**: Automates repository cloning and initiates scans upon detecting push events.
   
2. **[CAST GitSync](https://github.com/marketplace/gitrepofetcher)**: A GitHub app that provides the necessary permissions to access repositories and listen for push events. Refer to [this guide](https://docs.github.com/en/apps/using-github-apps/installing-a-github-app-from-github-marketplace-for-your-organizations) for installation instructions.

## Prerequisites

Ensure the following tools and software are installed:

1. **Git**: For cloning repositories. [Download Git](https://git-scm.com/).
2. **Python**: Version 3+ is required. The application is built using Flask. [Download Python](https://www.python.org/).
3. **pip**: To install required Python packages. Run:
   ```bash
   pip install Flask pandas requests fasteners openpyxl waitress pywin32
   ```
4. **ngrok**: Exposes the local server to the internet for webhook events. [Learn more about ngrok](https://ngrok.com/).
5. **Excel**: Required for creating repository mapping files.
6. **Install CAST GitSync**: [Get it here](https://github.com/marketplace/gitrepofetcher). Follow the guide to set it up at the organization or repository level.
7. **Strawberry Perl**: Required for specific scripts. [Download Strawberry Perl](https://strawberryperl.com/).

## Setup Instructions

### 1. Download the CAST Highlight GitHub Automator

Download the latest release from [here](https://github.com/hbe-cast/CAST-Highlight-GitHub-Automator/releases).

### 2. Download the Highlight Command Line Interface (HL CLI)

Get the HL CLI from the official [CAST Highlight download page](https://doc.casthighlight.com/product-tutorials-third-party-tools/automated-code-scan-command-line/).

### 3. Configuration

#### `config.json`

This file manages the connection between GitHub, ngrok, and CAST Highlight. Ensure all fields are filled correctly. You can get the `webhook_secret` and `authtoken` from your CAST representative.

#### `ngrok-config.yaml`

This file configures the ngrok connection. Ensure the `authtoken` and `domain` values are correctly set, and the `addr` field points to the port (e.g., `5001`) used by your Flask app.

### 4. Repository Mapping File

Ensure the `map/app_map.xlsx` file exists in the `CAST Highlight GitHub Automator` directory. The file format should look like this:

| app_name | unique_id      | github_url                   | highlight_app_id |
|----------|----------------|------------------------------|------------------|
| App1     | 7E876-879YUP   | https://github.com/user/app1  | 358776           |
| App2     | 7E876-879YUP   | https://github.com/user/app2  | 358776           |
| App3     | 87GHY-123HJ    | https://github.com/user/app3  | 358778           |

- **app_name**: The name of the application in CAST Highlight.
- **unique_id**: Repositories with the same unique_id are stored together.
- **github_url**: The repository URL.
- **highlight_app_id**: Unique ID from CAST Highlight.

> **Note**: Repositories without a `unique_id` will not be cloned, and the application will stop running.

### 5. Running the Service Installer

To install and run the CAST Highlight GitHub Automator as a Windows service:

1. Open a terminal with **Administrator** privileges.
2. Navigate to the `CAST Highlight GitHub Automator` directory.
3. Run:
   ```bash
   serviceInstaller.bat
   ```

This script will:
- Install the Python service using `MyService.py`.
- Start the service.
- Configure it to auto-start at boot.

### 6. Triggering Repository Scans

Whenever a push event occurs in a repository where the GitHub App is installed:
- The repository is cloned.
- A scan is initiated via the HL CLI.
- Results are uploaded to CAST Highlight as specified in `config.json`.

---

## Summary

The **CAST Highlight GitHub Automator** streamlines the process of cloning repositories and triggering scans automatically in response to push events.

### How It Works:

1. **GitHub App**: Configured to listen for push events.
2. **Webhook Handling**: GitHub sends event notifications to a public URL (via ngrok) that routes them to the Flask app.
3. **Verification**: The Flask app verifies the event using a shared webhook secret.
4. **Cloning**: The app clones the repository and initiates a scan.

### Architecture Overview:

- **GitHub App**: Listens for push events.
- **Flask Application**: Handles webhook events and manages repository cloning.
- **ngrok**: Exposes the Flask app to receive webhook events.
- **File System**: Repositories are cloned into unique directories based on their names.

### Key Components:

- **Webhook Secret**: Secures communication between GitHub and Flask.
- **Repository Configuration**: Managed through `repo_config.json`.
- **Cloning Logic**: Embedded in the Flask app to handle push events.