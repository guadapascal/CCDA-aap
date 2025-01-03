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
    
    {{
        "Lenguaje Inclusivo": {{
            "Puntuación": x,
            "Justificación": justificación breve del valor asignado para ese criterio."
        }},
        "Diversidad": {{
            "Puntuación": x,
            "Justificación": justificación breve del valor asignado para ese criterio."
        }},
        "Historia": {{
            "Puntuación": x,
            "Justificación": justificación breve del valor asignado para ese criterio."
        }},
        "Estereotipos": {{
            "Puntuación": x,
            "Justificación": justificación breve del valor asignado para ese criterio."
        }}
    }}
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
            temperature=0
        )
        # Obtener la respuesta de GPT
        evaluacion = response.choices[0].message.content.strip()
        #st.write(evaluacion)  # Mostrar la respuesta completa para debugging

        # Convertir la respuesta de GPT a un diccionario JSON
        evaluacion_json = json.loads(evaluacion)

        # Validar que se hayan devuelto todos los criterios
        if all(key in evaluacion_json for key in ["Lenguaje Inclusivo", "Diversidad", "Historia", "Estereotipos"]):
            st.success("Evaluación automática completada.")
            return evaluacion_json
        else:
            st.error("La respuesta no incluye todos los criterios esperados.")
            return {}

    except json.JSONDecodeError as e:
        st.error(f"Error al interpretar la respuesta del modelo como JSON: {e}")
        return {}
    except Exception as e:
        st.error(f"Error al interactuar con la API de OpenAI: {e}")
        return {}


# FLUJO DE LA APP

# Verificacion si `session_state` tiene las claves necesarias)
if "page_title" not in st.session_state:
    st.session_state["page_title"] = ""

if "post_content" not in st.session_state:
    st.session_state["post_content"] = ""

if "evaluacion" not in st.session_state:
    st.session_state["evaluacion"] = ""

if "evaluacion_json" not in st.session_state:
    st.session_state["evaluacion_json"] = ""

if "evaluacion_realizada" not in st.session_state:
    st.session_state["evaluacion_realizada"] = False

# ETAPA 1: Ingresar una contribución y realizar el scrapping
st.title("Análisis crítico y colaborativo de discursos")
st.subheader("1. Co-creación de la base de datos")

url = st.text_input("Ingresa la URL del posteo de la red social que quieres analizar:")

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
    #st.subheader("Resultado del Web Scraping")
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
            # Activar siguiente etapa 
            st.session_state["evaluacion_realizada"] = True
        else:
            st.warning("El contenido no es válido, lo revisaremos manualmente.")
            
# ETAPA 2: Aplicar la evaluación automática de la contribución
if st.session_state["evaluacion_realizada"] and st.session_state["post_content"]:
    st.subheader("2. Análisis automático")

    # Verificar si la evluación ya fue realizada
    if not st.session_state["evaluacion_json"]:
        st.write("Ponderación por criterio de la contribución")
        st.session_state["evaluacion_json"] = evaluar_contribucion(st.session_state["post_content"])
        st.json(st.session_state["evaluacion_json"])

        #Actualizar el registro con los resultados de la evaluación automática
        eval_data = [
            str(st.session_state["evaluacion_json"].get("Lenguaje Inclusivo", "")),
            str(st.session_state["evaluacion_json"].get("Diversidad", "")),
            str(st.session_state["evaluacion_json"].get("Historia", "")),
            str(st.session_state["evaluacion_json"].get("Estereotipos", ""))
        ]
        eval_columns = [5, 6, 7, 8]
        update_sheet(st.session_state["id_contribucion"], eval_data, eval_columns)
        st.success("Resultados de la evaluación automática guardados.")
    else:
        st.warning("No se puede realizar la evaluación automática en esta contribución. Lo revisaremos manualmente.")

elif not st.session_state["evaluacion_realizada"]:
    st.subheader("2. Análisis automático")
    st.info("Por favor confirma la validación del contenido para realizar la evaluación automática.")

# Inicializar `valores_corregidos` en session_state
if st.session_state["evaluacion_json"] and "valores_corregidos" not in st.session_state:
    st.session_state["valores_corregidos"] = {
        "Lenguaje Inclusivo": st.session_state["evaluacion_json"].get("Lenguaje Inclusivo", 1),
        "Diversidad": st.session_state["evaluacion_json"].get("Diversidad", 1),
        "Historia": st.session_state["evaluacion_json"].get("Historia", 1),
        "Estereotipos": st.session_state["evaluacion_json"].get("Estereotipos", 1),
    }

# Mostrar resultados y ajustar manualmente
if st.session_state["evaluacion_json"]:
    
    # ETAPA 2: Análisis automático.  
    st.subheader("2. Análisis automático")

    # Mostrar los resultados originales con sus justificaciones
    st.write("Valuación por criterio de la contribución")
    for criterio, datos in st.session_state["evaluacion_json"].items():
        st.write(f"**{criterio}:**")
        st.write(f"- **Puntuación:** {datos['Puntuación']}")
        st.write(f"- **Justificación:** {datos['Justificación']}")

    # ETAPA 3: Re-entrenando el algoritmo colectivamente.  
    st.subheader("3. Re-entrenando el algoritmo colectivamente")
    st.write("Modifica las poderaciones según tu mirada")
    
    # Inicializar los valores corregidos en `session_state` si no existen
    if "valores_corregidos" not in st.session_state:
        st.session_state["valores_corregidos"] = {
            criterio: datos["Puntuación"] for criterio, datos in st.session_state["evaluacion_json"].items()
        }

    # Mostrar sliders para ajustar cada criterio
    for criterio, datos in st.session_state["evaluacion_json"].items():
        st.session_state["valores_corregidos"][criterio] = st.slider(
            f"Ajustar {criterio}:", 
            min_value=1, 
            max_value=4, 
            value=datos["Puntuación"],  # Usamos "Puntuación" del JSON
            key=f"slider_{criterio}"
        )
    
    # Botón "Guardar evaluación ajustada"
    if st.button("Guardar Evaluación Ajustada"):
        if "valores_corregidos" in st.session_state:
            # Actualizar las columnas correspondientes en Google Sheets
            ajusted_data = [
                str(st.session_state["valores_corregidos"].get("Lenguaje Inclusivo", "")),
                str(st.session_state["valores_corregidos"].get("Diversidad", "")),
                str(st.session_state["valores_corregidos"].get("Historia", "")),
                str(st.session_state["valores_corregidos"].get("Estereotipos", ""))
            ]
            ajusted_columns = [9, 10, 11, 12]  # Columnas para los valores ajustados
            update_sheet(st.session_state["id_contribucion"], ajusted_data, ajusted_columns)
            st.success("Resultados ajustados guardados correctamente.")
        else:
            st.error("No se pudieron guardar los valores ajustados porque no están inicializados.")
        

        
        

