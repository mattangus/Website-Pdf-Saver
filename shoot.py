#Use this script to save a webpage as pdf. This can be scheduled to run daily by windows: https://stackoverflow.com/a/21502661/1097517

from selenium import webdriver
from io import BytesIO
import time
import shutil
import datetime
import json
import os
import logging
import re
import subprocess
import urllib
import urllib.request
import zipfile
import base64

# Change this URL if the website changes.
URL = 'https://www.gov.uk/guidance/coronavirus-covid-19-advice-for-uk-visa-applicants-and-temporary-uk-residents'
# Change this to change where the file should be saved. "." means this folder.
DOWNLOAD_FOLDER = "."

# set up the log file. It will append to the end.
logging.basicConfig(filename='shoot.log',
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

def run_process_with_output(cmd):
    p = subprocess.Popen(["chrome.bat"], stdout=subprocess.PIPE)
    out, _ = p.communicate()
    out = out.decode()

    return out


def get_chrome_version():
    out = run_process_with_output(["chrome.bat"])
    
    found = re.findall(r"\d+\.\d+\.\d+\.\d+", out)
    if len(found) == 0:
        logging.error("Could not find chrome version. manually download chromedriver.")
        return None
    return found[0]


def get_chrome_driver_version():
    out = run_process_with_output(["chromedriver.exe", "--version"])

    found = re.findall(r"\d+\.\d+\.\d+\.\d+", out)
    if len(found) == 0:
        logging.error("Could not find chrome version. manually download chromedriver.")
        return None
    return found[0]


def download_bytes(url):
    """
    Download a file to memory
    """
    response = urllib.request.urlopen(url)
    zippedData = response.read()
    tempIO = BytesIO()
    tempIO.write(zippedData)

    return tempIO


def download_chrome_driver():
    """
    Check for chrome version using chome.bat and then download the chromium version
    """
    chrome_version = get_chrome_version()
    if chrome_version is None:
        logging.error("Chrome not found. Install chrome")
        return
    
    logging.info(f"found chrome version '{chrome_version}'.")

    if os.path.exists("chromedriver.exe"):
        logging.info("chromedriver found. checking version.")
        driver_version = get_chrome_driver_version()
        logging.info(f"found chromedriver version '{driver_version}'")
        if driver_version == chrome_version:
            logging.info("versions are the same. Moving on.")
            return
    
    driver_url = f"https://chromedriver.storage.googleapis.com/{chrome_version}/chromedriver_win32.zip"
    logging.info(f"downloading driver from '{driver_url}'.")
    zip_data = download_bytes(driver_url)

    logging.info("unzipping")
    myzipfile = zipfile.ZipFile(zip_data)
    
    file_name = "chromedriver.exe"
    driverexe = myzipfile.open(file_name)

    logging.info(f"saving to {file_name}")
    with open(file_name, "wb") as f:
        f.write(driverexe.read())


def save_webpage(url, folder):
    # set up options for chrome
    appState = {
        "recentDestinations": [
            {
                "id": "Save as PDF",
                "origin": "local",
                "account": ""
            }
        ],
        "selectedDestinationId": "Save as PDF",
        "version": 2
    }
    profile = {'printing.print_preview_sticky_settings.appState': json.dumps(appState)}
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', profile)
    chrome_options.add_argument('--kiosk-printing')
    chrome_options.add_argument("--headless")

    logging.info("starting chrome")
    driver = webdriver.Chrome(options=chrome_options)

    logging.info(f"loading page {url}")
    driver.get(url)
    
    pdf = driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True
    })
    
    ouput = os.path.join(folder, datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S.pdf"))
    logging.info(f"saving file to '{ouput}'")

    with open(ouput, "wb") as f:
        f.write(base64.b64decode(pdf['data']))

def main():
    logging.info(("-" * 10) + "STARTING PROGRAM" + ("-" * 10))
    try:
        download_chrome_driver()
        save_webpage(URL, DOWNLOAD_FOLDER)
    except:
        import traceback
        tb = traceback.format_exc()
        logging.error(tb)
    logging.info(("-" * 10) + "ENDING PROGRAM" + ("-" * 10))

if __name__ == "__main__":
    main()
