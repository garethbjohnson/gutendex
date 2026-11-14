import requests
import os

URL = 'https://gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2'
DOWNLOAD_PATH = 'catalog.tar.bz2'

def download_file(url, path):
    print(f"Downloading {url} to {path}...")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            done = int(50 * downloaded / total_size)
                            print(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded}/{total_size}", end='')
            print("\nDownload complete.")
    except Exception as e:
        print(f"\nDownload failed: {e}")

if __name__ == "__main__":
    download_file(URL, DOWNLOAD_PATH)
    if os.path.exists(DOWNLOAD_PATH):
        print(f"File size: {os.path.getsize(DOWNLOAD_PATH)}")
        
