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
import openai
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configurar Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["google_drive"], scopes=SCOPES
)
sheet_service = build('sheets', 'v4', credentials=credentials)
SPREADSHEET_ID = '1NtXDHphN_SC6fmAb2Ni6tYJGb7CiRgGuYqMJbclwAr0'

# Configurar OpenAI
try:
    openai.api_key = st.secrets["openai_api_key"]
    st.write("Clave configurada correctamente.")
except Exception as e:
    st.error(f"Error al configurar la clave: {e}")

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
# Función para limpiar el texto
def limpiar_texto(texto):
    try:
        texto_limpio = json.dumps(texto)
        return json.loads(texto_limpio)
    except Exception as e:
        st.error(f"Error al procesar el contenido del texto: {e}")
        return ""

# Función para evaluar una contribución
def evaluar_contribucion(contribucion):
    prompt = f"""
    Eres un modelo que evalúa contenido en formato texto de redes sociales según criterios específicos:

    Este es el texto que debes analizar: {contribucion}
    
    Estos son los criterios y su escala de ponderación que debes seguir:  
    1. Uso de lenguaje inclusivo (1-4).
    2. Visibilización de la diversidad (1-4).
    3. Relevancia histórica y contexto (1-4).
    4. Ausencia de estereotipos de género (1-4).

    Devuelve los resultados en formato JSON:
    {{ "Lenguaje Inclusivo": x, "Diversidad": x, "Historia": x, "Estereotipos": x }}
    """
    try:
        texto_limpio = limpiar_texto(contribucion)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": texto_limpio},
            ],
            temperature=0.7
        )
        evaluacion = response["choices"][0]["message"]["content"]
        st.success("Evaluación automática completada")
        return evaluacion
    except Exception as e:
        st.error(f"Error al interactuar con la API de OpenAI: {e}")
        return {}


# Verificar si `session_state` tiene las claves necesarias
if "page_title" not in st.session_state:
    st.session_state["page_title"] = ""

if "post_content" not in st.session_state:
    st.session_state["post_content"] = ""

if "evaluacion" not in st.session_state:
    st.session_state["evaluacion"] = ""


# Entorno de la app
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

# Mostrar los resultados del scraping si están disponibles
if st.session_state["page_title"] or st.session_state["post_content"]:
    st.subheader("Resultado del Web Scraping")
    st.write(f"**Título de la Página:** {st.session_state['page_title']}")
    st.text_area("Contenido del Posteo:", st.session_state["post_content"], height=300)

    # Pregunta al usuario si el contenido es correcto
    is_correct = st.radio("¿El contenido extraído es correcto?", ("Sí", "No"), index=0)

    if st.button("Confirmar Validación"):
        if is_correct == "Sí":
            st.success("¡Gracias! El contenido ha sido validado correctamente.")

            # Verificar post_content y aplicar la evaluacion automática
            if "post_content" in st.session_state and st.session_state["post_content"]:
                st.session_state["evaluacion"] = evaluar_contribucion(st.session_state["post_content"])
                st.subheader("Resultados del GPT")
                st.json(st.session_state["evaluacion"])
            else:
                st.warning("El contenido del post no está disponible. Por favor, revisa el scraping.")
            
            # Preguntar corrección manual
            st.subheader("Ajustar los Valores")
            criterios = ["Lenguaje Inclusivo", "Diversidad", "Historia", "Estereotipos"]
            valores_corregidos = {}
            for criterio in criterios:
                valores_corregidos[criterio] = st.slider(
                    f"Ajustar {criterio}:", 1, 4, st.session_state["evaluacion"][criterio]
                )

            if st.button("Guardar Evaluación"):
                # Guardar en Google Sheets
                new_data = [[
                    url, st.session_state["page_title"], st.session_state["post_content"],
                    st.session_state["evaluacion"]["Lenguaje Inclusivo"], st.session_state["evaluacion"]["Diversidad"],
                    st.session_state["evaluacion"]["Historia"], st.session_state["evaluacion"]["Estereotipos"],
                    valores_corregidos["Lenguaje Inclusivo"], valores_corregidos["Diversidad"],
                    valores_corregidos["Historia"], valores_corregidos["Estereotipos"]
                ]]
                append_to_sheet(new_data)
                st.success("La evaluación ha sido guardada correctamente.")
        else:
            st.warning("Lamentablemente la app no logra recuperar automáticamente el contenido, lo revisaremos manualmente.")
        
        # Guardar los resultados en Google Sheets
        new_data = [[url, st.session_state["page_title"], st.session_state["post_content"], is_correct]]
        append_to_sheet(new_data)
        
        

