#!/usr/bin/env python3
"""
sync.py - Descarga un proyecto LaTeX de murfy.ai y lo guarda en ./project/.

Uso:
    python sync.py

Las credenciales se leen de un archivo .env (ver .env.example).
"""

import os
import sys
import time
import zipfile
import shutil
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

load_dotenv()

MURFY_URL = "https://murfy.ai"
EMAIL = os.environ.get("MURFY_EMAIL")
PASSWORD = os.environ.get("MURFY_PASSWORD")
PROJECT_NAME = os.environ.get("MURFY_PROJECT", "")

REPO_ROOT = Path(__file__).parent
DOWNLOAD_DIR = REPO_ROOT / "downloads"
OUTPUT_DIR = REPO_ROOT / "project"


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def validate_config():
    missing = [k for k, v in {"MURFY_EMAIL": EMAIL, "MURFY_PASSWORD": PASSWORD}.items() if not v]
    if missing:
        print(f"[ERROR] Variables de entorno faltantes: {', '.join(missing)}")
        print("Copiá .env.example a .env y completá tus credenciales.")
        sys.exit(1)


def make_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    # Modo browser visible (sin --headless).
    # Para ejecutar en GitHub Actions agregar: options.add_argument("--headless=new")
    options.add_experimental_option("prefs", {
        "download.default_directory": str(DOWNLOAD_DIR.resolve()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ---------------------------------------------------------------------------
# Pasos de la sincronización
# ---------------------------------------------------------------------------

def login(driver: webdriver.Chrome, wait: WebDriverWait):
    print("→ Navegando al login...")
    # TODO: confirmá la URL de login inspeccionando murfy.ai con DevTools.
    #       Opciones comunes: /en/login, /login, /sign-in
    driver.get(f"{MURFY_URL}/en/login")

    print("→ Completando credenciales...")
    try:
        # TODO: ajustá el selector si el campo email tiene otro name/id/type.
        #       Podés inspeccionarlo con DevTools (F12 → click en el campo → Copy selector).
        email_field = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='email'], input[name='email'], #email")
            )
        )
    except TimeoutException:
        print("[ERROR] No se encontró el campo de email. Verificá la URL de login y el selector.")
        raise

    email_field.clear()
    email_field.send_keys(EMAIL)

    # TODO: ajustá el selector del campo password si es necesario.
    password_field = driver.find_element(
        By.CSS_SELECTOR, "input[type='password'], input[name='password'], #password"
    )
    password_field.clear()
    password_field.send_keys(PASSWORD)

    # TODO: ajustá el selector del botón de submit si es necesario.
    submit_btn = driver.find_element(
        By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"
    )
    submit_btn.click()

    print("→ Esperando redirección post-login...")
    try:
        wait.until(EC.url_changes(driver.current_url))
        # TODO: cambiá este selector por un elemento que aparezca en el dashboard
        #       después del login (ej: lista de proyectos, barra de navegación, etc.).
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".project-list, [data-testid='project-list'], .dashboard, #project-list")
            )
        )
        print("   Login exitoso.")
    except TimeoutException:
        print("[ERROR] El login puede haber fallado o el selector del dashboard es incorrecto.")
        print(f"   URL actual: {driver.current_url}")
        raise


def find_and_open_project(driver: webdriver.Chrome, wait: WebDriverWait):
    if PROJECT_NAME:
        print(f"→ Buscando proyecto: {PROJECT_NAME!r}")
    else:
        print("→ Abriendo el primer proyecto de la lista...")

    try:
        if PROJECT_NAME:
            # TODO: ajustá el XPath si los proyectos no son <a> o usan otra estructura.
            project_link = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    f"//a[contains(., '{PROJECT_NAME}')] "
                    f"| //*[contains(@class,'project') and contains(.,'{PROJECT_NAME}')]"
                ))
            )
        else:
            # TODO: ajustá el selector para que apunte al primer ítem de proyecto.
            project_link = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".project-list a, [data-testid='project-name'], .project-item a")
                )
            )
        project_link.click()
        print("   Proyecto abierto.")
    except TimeoutException:
        print("[ERROR] No se encontró el proyecto. Revisá el nombre y los selectores del dashboard.")
        raise


def download_project_zip(driver: webdriver.Chrome, wait: WebDriverWait) -> Path:
    print("→ Esperando que cargue el editor...")
    # TODO: cambiá este selector por un elemento que indique que el editor cargó
    #       (ej: la barra de herramientas, el árbol de archivos, el área de código).
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".editor, #editor, [data-testid='editor'], .cm-editor")
            )
        )
    except TimeoutException:
        print("[ERROR] El editor no cargó. Revisá el selector del editor.")
        raise

    print("→ Abriendo menú para descargar ZIP...")
    # TODO: en Overleaf-like editors el flujo suele ser:
    #       1. Hacer clic en el botón "Menu" (esquina superior izquierda)
    #       2. Hacer clic en "Download ZIP" o "Export"
    #       Ajustá los selectores a lo que muestre murfy.ai.
    try:
        menu_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#main-menu, button.menu-btn, [aria-label='Menu'], [aria-label='menu']")
            )
        )
        menu_btn.click()
    except TimeoutException:
        print("[ERROR] No se encontró el botón de menú. Revisá el selector.")
        raise

    # TODO: ajustá el texto o selector del ítem de descarga.
    try:
        download_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//*[contains(text(),'Download') or contains(text(),'ZIP') "
                "or contains(text(),'Export') or contains(text(),'Descargar')]"
            ))
        )
        download_btn.click()
    except TimeoutException:
        print("[ERROR] No se encontró el botón de descarga. Revisá el selector.")
        raise

    print("→ Esperando que termine la descarga...")
    zip_path = _wait_for_download(DOWNLOAD_DIR)
    print(f"   Descargado: {zip_path.name}")
    return zip_path


def _wait_for_download(download_dir: Path, timeout: int = 60) -> Path:
    """Espera hasta que aparezca un .zip completamente descargado."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        completed = [
            f for f in download_dir.iterdir()
            if f.suffix == ".zip" and not f.name.endswith(".crdownload")
        ]
        if completed:
            return max(completed, key=lambda f: f.stat().st_mtime)
        time.sleep(1)
    raise TimeoutError(f"No apareció ningún .zip en {download_dir} tras {timeout}s.")


def extract_to_output(zip_path: Path):
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    print(f"→ Extrayendo {zip_path.name} → {OUTPUT_DIR.relative_to(REPO_ROOT)}/")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(OUTPUT_DIR)
    zip_path.unlink()
    print("   Listo.")


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main():
    validate_config()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    driver = make_driver()
    wait = WebDriverWait(driver, 20)
    try:
        login(driver, wait)
        find_and_open_project(driver, wait)
        zip_path = download_project_zip(driver, wait)
        extract_to_output(zip_path)
        print("\n✓ Proyecto sincronizado en ./project/")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
