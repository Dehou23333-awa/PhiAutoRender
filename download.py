import taptap
import os
import time

def download():
    url = taptap.taptap(165287)
    print(url)
    filename = "phigros.apk"
    retries = 3
    wait_time = 10
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    min_expected_size_bytes = 1024 * 1024 * 10  # Example: Minimum 10MB, adjust as needed

    for i in range(retries + 1):
        command = f"wget -O {filename} --user-agent='{user_agent}' '{url}'"
        result = os.system(command)
        if result == 0:
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"Download successful! File size: {file_size} bytes.")
                if file_size > min_expected_size_bytes:
                    break  # Break out of the loop if download seems complete
                else:
                    print(f"Warning: Downloaded file size is smaller than expected ({min_expected_size_bytes} bytes). Retrying...")
            else:
                print("Error: Download reported as successful, but file not found. Retrying...")
        else:
            print(f"Download failed (attempt {i+1}).")
            if i < retries:
                print(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Download failed.")
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    print(f"Partial download size: {file_size} bytes.")

if __name__ == "__main__":
    download()
