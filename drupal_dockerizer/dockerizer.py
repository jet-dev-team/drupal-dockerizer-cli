import requests
import os
import shutil
from zipfile import ZipFile

def initRepository(tag):
    url = f"https://codeload.github.com/jet-dev-team/drupal-dockerizer/zip/refs/heads/{tag}"
    r = requests.get(url)
    with open("drupal_dockerizer.zip", "wb") as code:
        code.write(r.content)
    with ZipFile("drupal_dockerizer.zip", "r") as zipObj:
        # Extract all the contents of zip file in current directory
        zipObj.extractall()
    os.remove("drupal_dockerizer.zip")
    shutil.copytree(
        f"drupal-dockerizer-{tag}", ".drupal_dockerizer", dirs_exist_ok=True
    )
    shutil.rmtree(f"drupal-dockerizer-{tag}")

