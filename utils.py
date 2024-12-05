import os
import subprocess
import tempfile
from time import sleep
from datetime import datetime


def view_html_in_browser(html_content):
    for script in html_content.find_all("script"):
        script.decompose()

    timestamp = int(datetime.now().timestamp())
    temp_file_name = f"temp_view_{timestamp}.html"
    temp_file_path = os.path.join(os.getcwd(), "temp", temp_file_name)

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
        temp_file.write(html_content.encode("utf-8"))
        temp_file_path = temp_file.name

    try:
        # Convert the WSL path to a Windows-compatible path
        windows_path = subprocess.check_output(["wslpath", "-w", temp_file_path]).decode().strip()
        subprocess.run(["cmd.exe", "/c", "start", windows_path], check=True)

    except Exception as e:
        print(f"Error opening file: {e}")
