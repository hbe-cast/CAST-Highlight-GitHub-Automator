import threading
import queue
import os
import hmac
import hashlib
import json
import logging
from flask import Flask, request, abort
from subprocess import run, PIPE, CalledProcessError
import pandas as pd
import requests
import fasteners
import shutil
import stat

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s', handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])
app = Flask(__name__)

# Load the configuration from a JSON file
with open('hbe-config.json') as config_file:
    config = json.load(config_file)

# Config Variables
BASE_TARGET_DIR = config['base_target_dir']
HIGHLIGHT_JAR_PATH = config['highlight_jar_path']
PERL_DIR = config['perl_dir']
ANALYZER_DIR = config['analyzer_dir']
WORKING_DIR = config['working_dir']
COMPANY_ID = config['companyId']
TOKEN_AUTH = config['tokenAuth']
WEBHOOK_SECRET = config['webhook_secret']
MAP_FILE = config['map_file']

# Global lock for handling concurrency
lock = fasteners.InterProcessLock('/tmp/clone_repository_lock')

# Initialize a queue
task_queue = queue.Queue()

# Worker thread function
def worker():
    while True:
        repo_url, base_target_dir = task_queue.get()
        try:
            clone_repository(repo_url, base_target_dir)
            logging.info(f"Task completed for {repo_url}")
        finally:
            task_queue.task_done()

# Start thread pool
num_worker_threads = 4  # Number of threads
for i in range(num_worker_threads):
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()

def handle_remove_readonly(func, path, exc_info):
    """
    Clear the read-only bit and reattempt the removal.
    This will handle the permission error for locked or read-only files.
    """
    logging.warning(f"Handling error for path: {path}")
    os.chmod(path, stat.S_IWRITE)  # Change the file to be writable
    func(path)  # Retry the function (in this case, os.unlink or os.rmdir)

def delete_existing_clone(unique_id_dir):
    """
    Delete the specific directory if it already exists.
    """
    if os.path.exists(unique_id_dir):
        try:
            shutil.rmtree(unique_id_dir, onerror=handle_remove_readonly)
            logging.info(f"Deleted existing directory: {unique_id_dir}")
        except Exception as e:
            logging.error(f"Failed to delete directory {unique_id_dir}: {e}")

def clone_repository(repo_url, base_target_dir):
    logging.info("========== Process Start ==========")
    logging.info("========== Reading App Mapping ==========")

    try:
        df = pd.read_excel(MAP_FILE, usecols="A:D", engine='openpyxl')
        df.columns = ['app_name', 'unique_id', 'github_url', 'highlight_app_id']
    except Exception as e:
        logging.error(f">>> ERROR: Error reading Excel file: {e}")
        return

    # Normalize repo_url by removing '.git' if present to match with 'github_url' in the Excel file
    normalized_repo_url = repo_url[:-4] if repo_url.endswith('.git') else repo_url

    # Match the normalized URL with the 'github_url' column in the DataFrame
    app_mapping_row = df[df['github_url'].str.strip() == normalized_repo_url.strip()]

    if app_mapping_row.empty:
        logging.warning(f">>> ERROR: No mapping found for the repository URL: {repo_url}")
        return

    if pd.isnull(app_mapping_row['highlight_app_id'].values[0]):
        logging.error(">>> ERROR: 'highlight_app_id' is missing. Please update the mapping with the HL App ID.")
        return

    try:
        application_id = int(str(app_mapping_row['highlight_app_id'].values[0]).strip())
    except ValueError:
        logging.error(">>> ERROR: 'highlight_app_id' value is not a valid integer. Please correct the ID format.")
        return

    # Verify highlight_app_id exists in CAST Highlight
    api_url = f"https://rpa.casthighlight.com/WS2/domains/{COMPANY_ID}/applications"
    headers = {'Authorization': f'Bearer {TOKEN_AUTH}'}
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        applications = response.json()
        if not any(app.get('id') == application_id for app in applications):
            logging.error(f">>> ERROR: CAST Application ID {application_id} doesn't exist. Please create the corresponding application in CAST Highlight.")
            return
    except requests.exceptions.HTTPError as e:
        logging.error(f">>> ERROR: HTTP error when contacting CAST Highlight API: {e.response.content}")
        return
    except requests.exceptions.RequestException as e:
        logging.error(f">>> ERROR: Failed to verify highlight_app_id against CAST Highlight API: {e}")
        return

    # Continue with cloning if highlight_app_id exists in CAST Highlight...
    unique_id = app_mapping_row['unique_id'].values[0]
    unique_id_dir = os.path.join(base_target_dir, str(unique_id))

    # Delete the specific directory if it already exists
    delete_existing_clone(unique_id_dir)

    # Now proceed to clone the repository into this directory
    try:
        logging.info(f"Starting cloning of repository from {repo_url} into {unique_id_dir}")
        run(['git', 'clone', repo_url, unique_id_dir], check=True, stderr=PIPE)
        logging.info(f'Repository cloned successfully into {unique_id_dir}')
    except CalledProcessError as e:
        logging.error(f'>>> ERROR: Failed to clone repository: {e}\n{e.stderr.decode()}')
        return False

    # Execute additional CLI commands if needed
    execute_cli_command(unique_id_dir, application_id)

    return True

def execute_cli_command(target_dir, application_id):
    logging.info("========== CLI: Importing to Highlight ==========")

    # Ensure the target directory uses forward slashes
    target_dir = target_dir.replace('\\', '/')

    # Change to the analyzer directory
    original_dir = os.getcwd()
    try:
        logging.info(f"Changing working directory to analyzer_dir: {ANALYZER_DIR}")
        os.chdir(ANALYZER_DIR)

        # Define the command
        command = [
            'java', '-jar', HIGHLIGHT_JAR_PATH,
            '--workingDir', WORKING_DIR,
            '--sourceDir', target_dir,
            '--perlInstallDir', PERL_DIR,
            '--companyId', COMPANY_ID,
            '--applicationId', str(application_id),
            '--tokenAuth', TOKEN_AUTH
        ]

        # Execute the command
        logging.info(f"Executing CLI command in {ANALYZER_DIR}")
        result = run(command, stdout=PIPE, stderr=PIPE, text=True)

        # Log the command output
        if result.stdout:
            logging.info(f'CLI command output: {result.stdout}')
        if result.stderr:
            logging.error(f'CLI command error output: {result.stderr}')

    except CalledProcessError as e:
        logging.error(f'>>> ERROR: Failed to execute CLI command: Return code {e.returncode}')
        if e.stdout:
            logging.error(f'>>> CLI command output: {e.stdout}')
        if e.stderr:
            logging.error(f'>>> CLI command error output: {e.stderr}')

    finally:
        os.chdir(original_dir)
        logging.info(f"Returned to original working directory: {original_dir}")

def verify_signature(request):
    signature = request.headers.get('X-Hub-Signature')
    if not signature:
        logging.error('Signature not found in headers')
        return False

    hmac_digest = hmac.new(WEBHOOK_SECRET.encode(), request.data, hashlib.sha1).hexdigest()

    if hmac.compare_digest(signature, 'sha1=' + hmac_digest):
        return True
    else:
        logging.error('Signature verification failed')
        return False

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    logging.info("Received a new webhook request")

    data = request.json
    repo_url = data.get('repository', {}).get('clone_url', 'Unknown Repo URL')
    logging.info(f"Processing repo URL: {repo_url}")

    commits = data.get('commits', [])
    logging.info(f"Number of commits: {len(commits)}")

    if lock.acquire(blocking=False):
        try:
            logging.info(f"Lock acquired for repo URL: {repo_url}")
            task_queue.put((repo_url, BASE_TARGET_DIR))
            return 'Webhook queued', 202
        finally:
            lock.release()
            logging.info(f"Lock released for repo URL: {repo_url}")
    else:
        error_message = f">>> ERROR: Concurrent processing prevented starting the process for: {repo_url}. Process skipped. Please try again later."
        logging.error(error_message)
        return 'Process skipped due to concurrency lock', 503

@app.errorhandler(400)
def bad_request(error):
    logging.error(f'Bad Request: {error}')
    return {'error': 'Bad request'}, 400

@app.errorhandler(404)
def not_found(error):
    logging.error(f'Not Found: {error}')
    return {'error': 'Not found'}, 404

@app.errorhandler(500)
def internal_server_error(error):
    logging.error(f'Internal Server Error: {error}')
    return {'error': 'Internal server error'}, 500

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logging.error(f'An unexpected error occurred: {error}')
    return {'error': 'An unexpected error occurred'}, 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
