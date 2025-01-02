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

def update_sheet(id_contribucion, data, columnas):
    try:
        # Convertir índices de columna a letras si es necesario
        if isinstance(columnas[0], int):
            columnas = [chr(65 + i) for i in columnas]  # Convertir a letras de columna (A, B, C, ...)

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
            # Generar el rango de actualización en formato válido
            start_column = columnas[0]
            end_column = columnas[-1]
            range_to_update = f"Hoja1!{start_column}{row_index}:{end_column}{row_index}"

            # Actualizar el registro existente
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
        st.error(f"Ups! Algo falló. No se pudo actualizar la base de datos: {e}")
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
            temperature=0.4
        )
        # Validar si el contenido de la respuesta existe
        evaluacion_json = response.choices[0].message.content.strip()

        # Mostrar la respuesta para depuración
        st.write("Respuesta de GPT:", evaluacion_json)

        # Validar que no esté vacío antes de intentar interpretarlo 
        if not evaluacion_json:
            raise ValueError("La respuesta de OpenAI está vacía.")

        # Intentar convertir la respuesta a JSON
        evaluacion = json.loads(evaluacion_json)
        st.success("Evaluación automática completada")
        return evaluacion
    except json.JSONDecodeError as e:
        st.error(f"Error al interpretar la respuesta del modelo como JSON: {e}")
        return {}
    except Exception as e:
        st.error(f"Error al interactuar con la API de OpenAI: {e}")
        return {}


# FLUJO DE LA APP

# ETAPA 1: Ingresar una contribución y realizar el scrapping
st.title("Validación de Contenidos de Redes Sociales")
url = st.text_input("Ingresa la URL del posteo de la red social:")

# Verificacion si `session_state` tiene las claves necesarias)
if "page_title" not in st.session_state:
    st.session_state["page_title"] = ""

if "post_content" not in st.session_state:
    st.session_state["post_content"] = ""

if "evaluacion" not in st.session_state:
    st.session_state["evaluacion"] = ""

# Botón "Procesar URL"
if url and st.button("Procesar URL"):
    try:
        # Generar un ID único
        if "id_contribucion" not in st.session_state:
            st.session_state["id_contribucion"] = create_id()
        
        # Validar datos
        if not isinstance(st.session_state["id_contribucion"], str):
            st.session_state["id_contribucion"] = str(st.session_state["id_contribucion"])
        if not isinstance(url, str):
            url = str(url)

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
    # Convertir los datos a cadenas antes de actualizar Google Sheets
        # Actualizar el registro con los datos de validación
        validation_data = [
            str(st.session_state["id_contribucion"]),  # ID único
            str(url),  # URL
            str(st.session_state["page_title"]),  # Título
            str(st.session_state["post_content"]),  # Contenido
            str(is_correct),  # Validación
        ]
        # Columnas para los datos
        validation_columns = [0, 1, 2, 3, 4]  # Índices para A, B, C, D, E
        update_sheet(
            st.session_state["id_contribucion"],
            validation_data,
            validation_columns
        )

        if is_correct == "Sí":
            st.success("El contenido ha sido validado correctamente.")
        
            # ETAPA 2: Aplicar la evaluación automática de la contribución
            if st.session_state["post_content"] and st.session_state["evaluacion"] == "":
                st.subheader("Evaluación automática de la contribución")
                st.session_state["evaluacion"] = evaluar_contribucion(st.session_state["post_content"])
                st.json(st.session_state["evaluacion"])

                # Actualizar el registro con los resultados de la evaluación automática
                eval_data = [
                    str(st.session_state["evaluacion"].get("Lenguaje Inclusivo", "")),
                    str(st.session_state["evaluacion"].get("Diversidad", "")),
                    str(st.session_state["evaluacion"].get("Historia", "")),
                    str(st.session_state["evaluacion"].get("Estereotipos", ""))
                ]
                eval_columns = [5, 6, 7, 8]
                update_sheet(st.session_state["id_contribucion"], eval_data, eval_columns)
                st.success("Resultados de la evaluación automática guardados.")
        
            else:
                st.warning("No se puede realizar la evaluación automática en esta contribución. Lo revisaremos manualmente.")

# Inicializar `valores_corregidos` en session_state
if st.session_state["evaluacion"] and "valores_corregidos" not in st.session_state:
    st.session_state["valores_corregidos"] = {
        "Lenguaje Inclusivo": st.session_state["evaluacion"].get("Lenguaje Inclusivo", 1),
        "Diversidad": st.session_state["evaluacion"].get("Diversidad", 1),
        "Historia": st.session_state["evaluacion"].get("Historia", 1),
        "Estereotipos": st.session_state["evaluacion"].get("Estereotipos", 1),
    }

# Mostrar reultados y permitir ajustarlos manualmente
if st.session_state["evaluacion"]:
    st.subheader("Resultados de la evaluación automática")
    st.json(st.session_state["evaluacion"])

    # Ajustar los valores manualmente mediante sliders
    st.subheader("Entrenando el algoritmo colectivamente")
    criterios = ["Lenguaje Inclusivo", "Diversidad", "Historia", "Estereotipos"]
    
    for criterio in criterios:
        st.session_state["valores_corregidos"][criterio] = st.slider(
            f"Ajustar {criterio}:",
            min_value = 1,
            max_value = 4,
            value = st.session_state["valores_corregidos"][criterio],
            key = f"slider_{criterio}"
        )
        
    # Botón "Guardar evaluación ajustada"
    if st.button("Guardar Evaluación Ajustada"):
        # Validar que los valores ajustados esten inicializados
        if "valores_corregidos" in st.session_state:
            ajusted_data = [
                str(st.session_state["valores_corregidos"]["Lenguaje Inclusivo"]),  # Convertir a cadena
                str(st.session_state["valores_corregidos"]["Diversidad"]),
                str(st.session_state["valores_corregidos"]["Historia"]),
                str(st.session_state["valores_corregidos"]["Estereotipos"])
            ]
            ajusted_columns = [9, 10, 11, 12]  # Columnas para los valores ajustados
            
            # Actualizar las columnas correspondientes en Google Sheets
            update_sheet(st.session_state["id_contribucion"], ajusted_data, ajusted_columns)
            st.success("Resultados ajustados guardados correctamente.")
        else:
            st.error("No se pudieron guardar los valores ajustados porque no están inicializados.")
        

        
        

