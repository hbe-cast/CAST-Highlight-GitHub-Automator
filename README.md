# My-Github-App Setup Guide

## Prerequisites

Before you start setting up My-Github-App, ensure you have the following prerequisites installed on your local machine:

1. **Git**: Needed to clone the My-Github-App repository. Download and install Git from [git-scm.com](https://git-scm.com/).

2. **Python**: The application is a Python-based Flask app. Ensure you have Python installed. You can download it from [python.org](https://www.python.org/). This guide assumes you are using Python 3.

3. **pip**: Python's package installer. It comes pre-installed with Python versions 3.4 and above. You'll need pip to install the required Python packages.

4. **ngrok**: Required to expose your local server to the internet for webhook events. Use the executable available in the repo which was downloaded from [ngrok.com](https://ngrok.com/).

5. **Excel**: The application requires an Excel file (`app_map.xlsx`) for repository mapping. Ensure you have Excel or a compatible spreadsheet program to create or edit this file.

6. **GitHub App**: If you need to set up the GitHub App, refer to the [GitHub App Setup Guide](github-app-setup.md).

After installing the prerequisites, follow the steps below to set up and run the My-Github-App on your local machine.

### 1. Cloning the Repository
Clone the `My-Github-App` repository to your local machine using the following command:
```bash
git clone git@github.com:hbe-cast/my-github-app.git
```

### 2. Downloading the Highlight Command Line Interface (HL CLI)
Download the HL CLI from the [official download page](https://doc.casthighlight.com/product-tutorials-third-party-tools/automated-code-scan-command-line/).

### 3. Setting Up HL CLI
After downloading, extract the `Highlight-Automation-Command.tar` file. Copy the contents of the extracted `perl` folder into the `My-Github-App` directory you cloned in step 1.

### 4. Configuring the Application
Update the `config.json` file with the necessary values. Ensure all fields are filled out correctly to avoid any issues during runtime.

### 5. Running the Application
Navigate to the `My-Github-App` directory in a terminal window and start the application by running:
```bash
python app.py
```

### 6. Establishing a Public Endpoint
Open a new terminal in the `My-Github-App` directory and execute the following command to create a public URL for your Flask application:
```bash
ngrok http 3000
```

This step uses [ngrok](https://ngrok.com/docs/) to expose your local server to the internet, enabling GitHub to trigger webhooks.

### 7. Preparing the Repository Mapping File
Ensure you have an Excel file named `app_map.xlsx` in the `My-Github-App` directory. The file should adhere to the following format:

| app_name      | troux_id    | gh_url                                      |
|---------------|-------------|---------------------------------------------|
| GitCloner     | 7E876-879YUP| https://github.com/hbe-cast/GitCloner       |
| GitCloner1    | 7E876-879YUP| https://github.com/hbe-cast/GitCloner_1     |
| WebGoat_test  | 87GHY-123HJ | https://github.com/hbe-cast/WebGoat_test    |

**Note:** Repositories without a `troux_id` will not be cloned, and the application will halt.

### 8. Triggering Scans
Whenever changes are pushed to a repository in your organization where the GitHub app is installed, it will trigger an event. This event clones the repository to your local machine and performs a scan using the HL CLI. The scan results are then uploaded to the Highlight instance specified in the `repo_config.json` file.

# Summary Details of the GitHub App

We've developed an integration between a GitHub App and a Flask-based web application that automates the cloning of repositories into a specified directory on a server or local machine whenever a "push" event occurs in any of the repositories where the GitHub App is installed.

### How It Works:

1. **GitHub App Setup**: A GitHub App was created and configured with permissions to access repository contents. It was set to receive webhook events, specifically "push" events, from repositories where the App is installed.

2. **Webhook Configuration**: The GitHub App's webhook is configured to send event notifications to a publicly accessible URL, which points to our Flask application. For local development and testing, we used `ngrok` to expose the local server to the internet.

3. **Event Handling**: When a push event occurs in a repository, GitHub sends a webhook event to the Flask application. The event contains details about the push, including the repository's clone URL.

4. **Verification**: Upon receiving a webhook event, the Flask app verifies the event's authenticity using a shared secret (the webhook secret set in the GitHub App settings) to ensure it's a legitimate request from GitHub.

5. **Cloning Operation**: After verification, the Flask app extracts the repository's clone URL from the webhook payload and performs a `git clone` operation, saving the repository contents to a pre-configured directory on the server or local machine.

### Architecture:

- **GitHub App**: Serves as the interface between GitHub repositories and the Flask application. It's configured to listen for push events and send notifications to the Flask app via webhooks.

- **Flask Web Application**: Acts as a webhook server that listens for incoming webhook events from the GitHub App. It contains logic to verify webhook payloads, extract necessary information, and execute repository cloning operations.

- **`ngrok`/Public URL**: Provides a bridge between GitHub and the Flask application running on a local machine or private network, making the Flask app's webhook endpoint accessible from the internet.

- **File System/Target Directory**: The location on the server or local machine where the repositories are cloned. Each repository is cloned into a unique subdirectory within this base directory, based on the repository's name.

### Key Components:

- **Webhook Secret**: Used to secure and verify the communication between GitHub and the Flask application, ensuring that webhook events are authentic.

- **`repo_config.json` Configuration File**: Contains configurable parameters for the Flask app, such as the base target directory for cloning operations.

- **Cloning Logic**: Embedded within the Flask app, this logic handles the cloning of repositories using the `git clone` command, triggered by validated push events from GitHub.

This setup automates the cloning of repositories, ensuring that the latest changes are always mirrored in the specified directory on the server or local machine, facilitating a seamless workflow for managing and archiving repository contents in response to development activities.