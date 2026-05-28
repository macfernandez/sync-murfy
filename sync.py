#!/usr/bin/env python3
"""
sync.py - Download a Murfy LaTeX project as a ZIP file.

Usage:
    python sync.py

Credentials are loaded from a .env file (see .env.example).
The downloaded ZIP is saved to ./downloads/{project-name}.zip.
"""

import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

load_dotenv()

MURFY_URL = "https://app.murfy.ai"
EMAIL = os.environ.get("MURFY_EMAIL")
PASSWORD = os.environ.get("MURFY_PASSWORD")
PROJECT_NAME = os.environ.get("MURFY_PROJECT", "")

REPO_ROOT = Path(__file__).parent
DOWNLOAD_DIR = REPO_ROOT / "downloads"


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def validate_config():
    missing = [k for k, v in {"MURFY_EMAIL": EMAIL, "MURFY_PASSWORD": PASSWORD}.items() if not v]
    if missing:
        log.error("Missing environment variables: %s", ", ".join(missing))
        log.error("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)


def make_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    # Visible browser mode (no --headless flag).
    # For GitHub Actions add: options.add_argument("--headless=new")
    options.add_experimental_option("prefs", {
        "download.default_directory": str(DOWNLOAD_DIR.resolve()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ---------------------------------------------------------------------------
# Sync steps
# ---------------------------------------------------------------------------

def login(driver: webdriver.Chrome, wait: WebDriverWait):
    log.info("Navigating to login page...")
    driver.get(MURFY_URL)

    log.info("Filling in credentials...")
    try:
        email_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
    except TimeoutException:
        log.error("Email field not found. Check the login URL and selector.")
        raise

    email_field.clear()
    email_field.send_keys(EMAIL)

    password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    password_field.clear()
    password_field.send_keys(PASSWORD)

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    submit_btn.click()

    log.info("Waiting for post-login redirect...")
    try:
        wait.until(EC.url_changes(driver.current_url))
        log.info("Login successful. Current URL: %s", driver.current_url)
    except TimeoutException:
        log.error("Login may have failed. Current URL: %s", driver.current_url)
        raise


def find_and_download_project(wait: WebDriverWait) -> Path:
    if PROJECT_NAME:
        log.info("Looking for project: %r", PROJECT_NAME)
        row_xpath = f"//tr[.//span[@title='{PROJECT_NAME}']]"
    else:
        log.info("No project name set — using the first project in the list.")
        row_xpath = "(//tr[.//span[@title]])[1]"

    try:
        row = wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))
    except TimeoutException:
        log.error("Project not found. Check the value of MURFY_PROJECT.")
        raise

    log.info("Opening project context menu...")
    try:
        ellipsis_btn = row.find_element(By.CSS_SELECTOR, "button[aria-haspopup='menu']")
        ellipsis_btn.click()
    except NoSuchElementException:
        log.error("Could not find the ⋯ button for the project row.")
        raise

    try:
        download_item = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@role='menuitem'][.//span[text()='Download']]",
            ))
        )
        download_item.click()
    except TimeoutException:
        log.error("'Download' option not found in the context menu.")
        raise

    log.info("Waiting for download to complete...")
    zip_path = _wait_for_download(DOWNLOAD_DIR)

    # Rename to {project-name}.zip for a predictable filename.
    # Falls back to the original name if PROJECT_NAME is not set.
    if PROJECT_NAME:
        target = DOWNLOAD_DIR / f"{PROJECT_NAME}.zip"
        zip_path = zip_path.rename(target)

    log.info("ZIP saved to: %s", zip_path)
    return zip_path


def _wait_for_download(download_dir: Path, timeout: int = 60) -> Path:
    """Poll download_dir until a fully written .zip file appears."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        completed = [
            f for f in download_dir.iterdir()
            if f.suffix == ".zip" and not f.name.endswith(".crdownload")
        ]
        if completed:
            return max(completed, key=lambda f: f.stat().st_mtime)
        time.sleep(1)
    raise TimeoutError(f"No .zip file appeared in {download_dir} within {timeout}s.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    validate_config()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    driver = make_driver()
    wait = WebDriverWait(driver, 20)
    try:
        login(driver, wait)
        find_and_download_project(wait)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
