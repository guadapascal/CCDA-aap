import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configurar la autenticación de Google Sheets utilizando secrets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["google_drive"], scopes=SCOPES
)
sheet_service = build('sheets', 'v4', credentials=credentials)

# ID de la hoja de cálculo
SPREADSHEET_ID = '1NtXDHphN_SC6fmAb2Ni6tYJGb7CiRgGuYqMJbclwAr0'

# Función para agregar datos a Google Sheets
def append_to_sheet(data):
    try:
        sheet = sheet_service.spreadsheets()
        body = {'values': data}
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Hoja1!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        st.write("Datos guardados exitosamente en Google Sheets.")  # Mensaje de debug
        return result
    except Exception as e:
        st.error(f"No se pudo actualizar Google Sheets: {e}")
        print(e)  # Mensaje de debug

# Función para inicializar el driver de Selenium
def get_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")  # Ejecutar sin interfaz gráfica
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=options,
    )

# Verificar si `session_state` tiene las claves necesarias
if "page_title" not in st.session_state:
    st.session_state["page_title"] = ""
if "post_content" not in st.session_state:
    st.session_state["post_content"] = ""

# Diseño de la app
st.title("Validación de Contenidos de Redes Sociales")

url = st.text_input("Ingresa la URL del posteo de la red social:")

if url and st.button("Procesar URL"):
        try:
            driver = get_driver()
            driver.set_page_load_timeout(30)  # Incrementar tiempo de espera
            driver.get(url)

            # Extraer el título
            st.session_state["page_title"] = driver.title

            # Extraer el contenido del posteo
            try:
                # Usar WebDriverWait para esperar el contenido
                st.session_state["post_content"] = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, '_a9zs')]"))
                ).text
            except Exception:
                st.session_state["post_content"] = "No se pudo extraer el contenido del posteo."

        except Exception as e:
            st.error(f"Hubo un error al intentar hacer web scraping: {e}")

        finally:
            # Cerrar el navegador
            if "driver" in locals():
                driver.quit()

# Mostrar resultados si ya están almacenados
if st.session_state["page_title"] and st.session_state["post_content"]:
    st.subheader("Resultado del Web Scraping")
    st.write(f"**Título de la Página:** {st.session_state['page_title']}")
    st.text_area("Contenido del Posteo:", st.session_state["post_content"], height=300)

    # Pregunta al usuario
    is_correct = st.radio("¿El contenido extraído es correcto?", ("Sí", "No"), index=0)
    if st.button("Confirmar Validación"):
        if is_correct == "Sí":
            st.success("¡Gracias! El contenido ha sido validado correctamente.")
        else:
            st.warning("Lamentablemente la app no logra recuperar automáticamente el contenido, lo revisaremos manualmente.")

        # Guardar los resultados en Google Sheets
        new_data = [[url, st.session_state["page_title"], st.session_state["post_content"], is_correct]]
        append_to_sheet(new_data)
        
        

