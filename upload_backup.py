#!/usr/bin/env python3
import paramiko
import os
import sys

# Windows path
LOCAL_PATH = r"D:\CODEX\STEPHANS OG\stephans-pet-app\Stephans_2026-01-27_12-19-23.zip"
REMOTE_PATH = "/tmp/restore_source.zip"

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    if not os.path.exists(LOCAL_PATH):
        print(f"Error: Local file {LOCAL_PATH} not found.")
        return

    print(f"Uploading {LOCAL_PATH} to {HOST}:{REMOTE_PATH}...")
    try:
        transport = paramiko.Transport((HOST, 22))
        transport.connect(username=USER, password=PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Callback for progress
        def progress(transferred, total):
            sys.stdout.write(f"\rTransferred: {transferred/1024/1024:.2f} MB of {total/1024/1024:.2f} MB")
            sys.stdout.flush()

        sftp.put(LOCAL_PATH, REMOTE_PATH, callback=progress)
        print("\nUpload complete.")
        sftp.close()
        transport.close()
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
