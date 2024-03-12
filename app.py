import os
import hmac
import hashlib
import json
from flask import Flask, request, abort
from subprocess import run, CalledProcessError
import pandas as pd

app = Flask(__name__)

# Load the configuration from a JSON file
with open('config.json') as config_file:
    config = json.load(config_file)

# Config Variables
BASE_TARGET_DIR = config['base_target_dir']
HIGHLIGHT_JAR_PATH = config['highlight_jar_path']
WORKING_DIR = config['working_dir']
COMPANY_ID = config['companyId']
APPLICATION_ID = config['applicationId']
TOKEN_AUTH = config['tokenAuth']
WEBHOOK_SECRET = config['webhook_secret']  # Webhook Secret from GitHub
MAP_FILE = config['map_file']

def clone_repository(repo_url, base_target_dir, target_dir):
    # Read the Excel file
    df = pd.read_excel(MAP_FILE, usecols="B:C", engine='openpyxl')
    df.columns = ['Troux_ID', 'GitHub_URL']

    # Normalize the repo_url by removing '.git' if present
    normalized_repo_url = repo_url[:-4] if repo_url.endswith('.git') else repo_url

    # Find the Troux ID associated with the normalized_repo_url
    troux_id_row = df[df['GitHub_URL'] == normalized_repo_url]

    if troux_id_row.empty or pd.isnull(troux_id_row['Troux_ID'].values[0]):
        print(f"No valid Troux ID found for the repository URL: {repo_url}")
        return

    troux_id = troux_id_row['Troux_ID'].values[0]  # Assuming the first matching Troux ID is what we want

    # Proceed only if Troux ID is valid
    if not pd.isna(troux_id):
        troux_id_dir = os.path.join(base_target_dir, str(troux_id))
        if not os.path.exists(troux_id_dir):
            os.makedirs(troux_id_dir)
            print(f"Created parent directory: {troux_id_dir}")

        # Filter the DataFrame for rows with the same Troux ID
        same_troux_id_df = df[df['Troux_ID'] == troux_id]

        for _, row in same_troux_id_df.iterrows():
            git_url = row['GitHub_URL']
            repo_name = git_url.split('/')[-1]  # Extract the repo name from the URL
            repo_target_dir = os.path.join(troux_id_dir, repo_name)  # Directory for each repo within the Troux_ID parent folder

            # Clone each repository into its directory within the Troux_ID parent folder
            try:
                print(f"Starting cloning of repository from {git_url} into {repo_target_dir}")
                run(['git', 'clone', git_url, repo_target_dir], check=True)
                print(f'Repository cloned successfully into {repo_target_dir}')
            except CalledProcessError as e:
                print(f'Failed to clone repository: {e}')
        
        # Execute the CLI
        execute_cli_command(troux_id_dir)
    else:
        print(f"No valid Troux ID found for the repository URL: {repo_url}")

def execute_cli_command(target_dir):
    try:
        command = [
            'java', '-jar', HIGHLIGHT_JAR_PATH, 
            '--workingDir', WORKING_DIR, 
            '--sourceDir', target_dir,
            '--companyId', COMPANY_ID,
            '--applicationId', APPLICATION_ID,
            '--tokenAuth', TOKEN_AUTH
        ]
        print(f"Executing CLI command in {target_dir}")
        run(command, check=True)
        print('CLI command executed successfully')
    except CalledProcessError as e:
        print(f'Failed to execute CLI command: {e}')

def verify_signature(request):
    signature = request.headers.get('X-Hub-Signature')
    hmac_digest = hmac.new(WEBHOOK_SECRET.encode(), request.data, hashlib.sha1).hexdigest()
    return hmac.compare_digest(signature, 'sha1=' + hmac_digest)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    if not verify_signature(request):
        abort(400, 'Invalid signature')

    data = request.json
    repo_url = data['repository']['clone_url']
    base_target_dir = BASE_TARGET_DIR
    target_dir = BASE_TARGET_DIR

    clone_repository(repo_url, base_target_dir, target_dir)

    return 'Webhook processed', 200

if __name__ == '__main__':
    app.run(port=3000, debug=True)
