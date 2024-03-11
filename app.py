import os
import hmac
import hashlib
import json
from flask import Flask, request, abort
from subprocess import run, CalledProcessError

app = Flask(__name__)

# Load the configuration from a JSON file
with open('repo_config.json') as config_file:
    config = json.load(config_file)
BASE_TARGET_DIR = config['base_target_dir']
HIGHLIGHT_JAR_PATH = config['highlight_jar_path']
WORKING_DIR = config['working_dir']
PERL_INSTALL_DIR = config['perl_install_dir']  # Load the Perl installation directory

# Hardcoding the WEBHOOK_SECRET for troubleshooting
WEBHOOK_SECRET = 'w6uHzbeW4ZKMkfVShdj8rR'

def clone_repository(repo_url, target_dir):
    try:
        run(['git', 'clone', repo_url, target_dir], check=True)
        print(f'Repository cloned successfully into {target_dir}')
        execute_cli_command(target_dir)
    except CalledProcessError as e:
        print(f'Failed to clone repository: {e}')

def execute_cli_command(target_dir):
    try:
        command = [
            'java', '-jar', HIGHLIGHT_JAR_PATH, 
            '--workingDir', WORKING_DIR, 
            '--sourceDir', target_dir,
            '--perlInstallDir', PERL_INSTALL_DIR,  # Perl
            '--skipUpload'
        ]
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
    repo_name = data['repository']['name']
    target_dir = os.path.join(BASE_TARGET_DIR, repo_name)

    clone_repository(repo_url, target_dir)

    return 'Webhook processed', 200

if __name__ == '__main__':
    app.run(port=3000, debug=True)
