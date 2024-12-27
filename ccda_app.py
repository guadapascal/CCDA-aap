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
from openai import OpenAI
import openai
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import uuid

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

client = OpenAI(
    api_key=os.environ.get("openai_api_key"),
)

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

# Función para generar un ID único
def create_id():
    return str(uuid.uuid4())  

# Función para limpiar el texto
def limpiar_texto(texto):
    try:
        texto_limpio = json.dumps(texto)
        return json.loads(texto_limpio)
    except Exception as e:
        st.error(f"Error al procesar el contenido del texto: {e}")
        return ""

# Función para agregar datos a Google Sheets
def update_sheet(id_contribucion, data, columnas):
    try:
        # Leer todas las filas existentes en la hoja
        sheet = sheet_service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Hoja1"
        ).execute()
        values = result.get("values", [])

        # Buscar el registro basado en `ID_contribucion`
        row_index = None
        for i, row in enumerate(values):
            if row and row[0] == id_contribucion:  # Asume que el ID está en la primera columna
                row_index = i + 1  # La API de Google Sheets usa índices basados en 1
                break

        if row_index:
            # Actualizar el registro existente
            range_to_update = f"Hoja1!A{row_index}:{chr(65 + len(columnas) - 1)}{row_index}"
            body = {"values": [data]}
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_to_update,
                valueInputOption="RAW",
                body=body
            ).execute()
            st.success("El registro existente ha sido actualizado correctamente.")
        else:
            # Crear un nuevo registro con las columnas especificadas
            body = {"values": [data]}
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range="Hoja1",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
            st.success("El registro ha sido agregado correctamente.")
    except Exception as e:
        st.error(f"No se pudo actualizar Google Sheets: {e}")
        print(e)


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
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user", 
                    "content": prompt,
                }
            ],
            temperature=0.7
        )
        evaluacion_json = response.choices[0].message.content
        evaluacion = json.loads(evaluacion_json)
        st.success("Evaluación automática completada")
        return evaluacion
    except json.JSONDecodeError as e:
        st.error(f"Error al interpretar la respuesta del modelo como JSON: {e}")
        return {}
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


# Entorno de la app: web scrapping
st.title("Validación de Contenidos de Redes Sociales")
url = st.text_input("Ingresa la URL del posteo de la red social:")


# Botón "Procesar URL"
if url and st.button("Procesar URL"):
    try:
        # Generar un ID único
        if "id_contribucion" not in st.session_state:
            st.session_state["id_contribucion"] = create_id()

        # Crear el registro inicial con ID y URL
        initial_data = [st.session_state["id_contribucion"], url]
        update_sheet(
            st.session_state["id_contribucion"], initial_data, ["ID_contribucion", "URL"]
        )

        # Realizar web scraping
        driver = get_driver()
        driver.set_page_load_timeout(30)
        driver.get(url)

        # Extraer el título
        st.session_state["page_title"] = driver.title

        # Extraer el contenido del posteo
        try:
            st.session_state["post_content"] = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, '_a9zs')]"))
            ).text
        except Exception:
            st.session_state["post_content"] = "No se pudo extraer el contenido del posteo."
        st.success("Web scraping completado.")
    except Exception as e:
        st.error(f"Hubo un error al intentar hacer web scraping: {e}")
    finally:
        if "driver" in locals():
            driver.quit()

# Botón "Confirmar Validación"
if st.session_state["page_title"] or st.session_state["post_content"]:
    st.subheader("Resultado del Web Scraping")
    st.write(f"**Título de la Página:** {st.session_state['page_title']}")
    st.text_area("Contenido del Posteo:", st.session_state["post_content"], height=300)

    # Preguntar al usuario si el contenido es correcto
    is_correct = st.radio("¿El contenido extraído es correcto?", ("Sí", "No"), index=0)

    if st.button("Confirmar Validación"):
        # Actualizar el registro con datos adicionales
        validation_data = [
            st.session_state["id_contribucion"],  # ID único
            url,  # URL
            st.session_state["page_title"],  # Título
            st.session_state["post_content"],  # Contenido
            is_correct,  # Validación
        ]
        update_sheet(
            st.session_state["id_contribucion"], validation_data,
            ["ID_contribucion", "URL", "Título", "Contenido", "Validación"]
        )
        if is_correct == "Sí":
            st.success("El contenido ha sido validado correctamente.")
            
            # Aplicar la evaluacion automática
            if "post_content" in st.session_state and st.session_state["post_content"]:
                st.session_state["evaluacion"] = evaluar_contribucion(st.session_state["post_content"])
                st.subheader("Resultados de la evaluación automática")
                st.json(st.session_state["evaluacion"])
            else:
                st.warning("No se puede realizar la evaluación automática en esta contribución. Lo revisaremos manualmente.")
            
            # Inicializar los valores de los criterios en `session_state`
            if "valores_corregidos" not in st.session_state:
                st.session_state["valores_corregidos"] = {
                    "Lenguaje Inclusivo": st.session_state["evaluacion"].get("Lenguaje Inclusivo", 1),
                    "Diversidad": st.session_state["evaluacion"].get("Diversidad", 1),
                    "Historia": st.session_state["evaluacion"].get("Historia", 1),
                    "Estereotipos": st.session_state["evaluacion"].get("Estereotipos", 1),
                }     
        else:
            st.warning("Lamentablemente el contenido no es válido, lo revisaremos manualmente.")

# Ajustar los criterios manualmente
if st.session_state["evaluacion"]:
    st.subheader("Entrenando el algoritmo colectivamente")

    # Diccionario para almacenar los valores corregidos
    if "valores_corregidos" not in st.session_state:
        st.session_state["valores_corregidos"] = {
            "Lenguaje Inclusivo": st.session_state["evaluacion"]["Lenguaje Inclusivo"],
            "Diversidad": st.session_state["evaluacion"]["Diversidad"],
            "Historia": st.session_state["evaluacion"]["Historia"],
            "Estereotipos": st.session_state["evaluacion"]["Estereotipos"],
        }

    # Mostrar sliders para cada criterio
    for criterio, valor in st.session_state["valores_corregidos"].items():
        st.session_state["valores_corregidos"][criterio] = st.slider(
            f"Ajustar {criterio}:",
            min_value=1,
            max_value=4,
            value=st.session_state["valores_corregidos"][criterio],
            key=f"slider_{criterio}"
        )
        
    # Botón para guardar la evaluación ajustada
    if st.button("Guardar Evaluación", key = "guardar_evaluacion"):
        # Consolifar datos para guardar en Google Sheets
        new_data = [[
            url, 
            st.session_state["page_title"], 
            st.session_state["post_content"],
            st.session_state["evaluacion"]["Lenguaje Inclusivo"], 
            st.session_state["evaluacion"]["Diversidad"],
            st.session_state["evaluacion"]["Historia"], 
            st.session_state["evaluacion"]["Estereotipos"],
            st.session_state["valores_corregidos"]["Lenguaje Inclusivo"], 
            st.session_state["valores_corregidos"]["Diversidad"],
            st.session_state["valores_corregidos"]["Historia"], 
            st.session_state["valores_corregidos"]["Estereotipos"]
        ]]
        append_to_sheet(new_data)
        st.success("La evaluación ha sido guardada correctamente.")
    else:
        st.warning("Lamentablemente algo falló. Lo revisaremos manualmente.")
        
        # Guardar los resultados en Google Sheets
        #new_data = [[url, st.session_state["page_title"], st.session_state["post_content"], is_correct]]
        #append_to_sheet(new_data)
        
        

