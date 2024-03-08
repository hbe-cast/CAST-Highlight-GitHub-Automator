import os
import hmac
import hashlib
import json
from flask import Flask, request, abort
from subprocess import run, CalledProcessError

app = Flask(__name__)

# Load the configuration from a JSON file or environment variable
with open('repo_config.json') as config_file:
    config = json.load(config_file)
BASE_TARGET_DIR = config['base_target_dir']
# WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET') # to set global variable

# Hardcoding the WEBHOOK_SECRET for troubleshooting
WEBHOOK_SECRET = 'w6uHzbeW4ZKMkfVShdj8rR'

def clone_repository(repo_url, target_dir):
    try:
        # Clone the repository using the 'git clone' command
        run(['git', 'clone', repo_url, target_dir], check=True)
        print(f'Repository cloned successfully into {target_dir}')
    except CalledProcessError as e:
        print(f'Failed to clone repository: {e}')

def verify_signature(request):
    
    #if WEBHOOK_SECRET is None:
    #    print("WEBHOOK_SECRET is not set.")
    #    abort(500, "Server configuration error.")
    #    print(f"WEBHOOK_SECRET: {WEBHOOK_SECRET}")

    # Get the signature from the request headers
    signature = request.headers.get('X-Hub-Signature')
    
    # Compute the HMAC hex digest
    hmac_digest = hmac.new(WEBHOOK_SECRET.encode(), request.data, hashlib.sha1).hexdigest()
    
    # Verify if the computed digest matches the provided signature
    return hmac.compare_digest(signature, 'sha1=' + hmac_digest)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # First, verify the webhook signature
    if not verify_signature(request):
        abort(400, 'Invalid signature')

    # Parse the webhook payload
    data = request.json
    repo_url = data['repository']['clone_url']  # Get the clone URL from the webhook payload
    repo_name = data['repository']['name']  # Get the repository name

    # Construct the target directory path
    target_dir = os.path.join(BASE_TARGET_DIR, repo_name)

    # Clone the repository
    clone_repository(repo_url, target_dir)

    return 'Webhook processed', 200

if __name__ == '__main__':
    app.run(port=3000, debug=True)
