import os
from pathlib import Path
import paramiko
from scp import SCPClient
from dotenv import load_dotenv

# Load environment variables
# Assuming .env is in the same directory or project root
load_dotenv() 

def publish_file(local_file_path):
    """
    Uploads a single file to the remote server defined in .env.
    """
    # 1. Get Configuration
    host = os.getenv('TARGET_HOST')
    port = int(os.getenv('TARGET_PORT', 22))
    user = os.getenv('SSH_USER')
    # Use key_filename if you have SSH keys set up (recommended), else password
    password = os.getenv('SSH_PASSWORD') 
    remote_dest_dir = os.getenv('REMOTE_DEST_PATH')

    if not os.path.exists(local_file_path):
        print(f"❌ Error: Local file not found: {local_file_path}")
        return

    try:
        # 2. Establish SSH Connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"🔌 Connecting to {host}:{port}...")
        ssh.connect(host, port=port, username=user, password=password)

        # 3. Transfer File
        with SCPClient(ssh.get_transport()) as scp:
            print(f"🚀 Uploading {os.path.basename(local_file_path)} to {remote_dest_dir}...")
            
            # scp.put(source, destination)
            # This will automatically overwrite the file if it exists on the remote
            scp.put(local_file_path, remote_path=remote_dest_dir)
            
        ssh.close()
        print("✅ Upload complete.")
        
    except Exception as e:
        print(f"❌ Transfer Failed: {e}")

if __name__ == "__main__":
    # Define the path to your specific file
    # Adjust this path if the html file is in a specific results folder
    MAP_FILE = "snow_conditions_map.html"
    
    publish_file(MAP_FILE)