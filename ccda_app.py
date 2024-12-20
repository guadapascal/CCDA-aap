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
# Archivo CSV donde se guardarán las respuestas
csv_file = "revisiones.csv"

# Crear el archivo CSV si no existe
if not os.path.exists(csv_file):
    df = pd.DataFrame(columns=["ID", "URL", "Título", "Contenido", "Correcto"])
    df.to_csv(csv_file, index=False)

# Entorno de la app
st.title("Validación de Contenidos de Redes Sociales")

url = st.text_input("Ingresa la URL del posteo de la red social:")

if url:
    if st.button("Procesar URL"):
        try:
            driver = get_driver()
            driver.set_page_load_timeout(30)  # Incrementar tiempo de espera
            driver.get(url)

            # Extraer el título
            page_title = driver.title

            # Extraer el contenido del posteo
            try:
                # Usar WebDriverWait para esperar el contenido
                post_content = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, '_a9zs')]"))
                ).text
            except Exception:
                post_content = "No se pudo extraer el contenido del posteo."

            # Mostrar resultados
            st.subheader("Resultado del Web Scraping")
            st.write(f"**Título de la Página:** {page_title}")
            st.text_area("Contenido del Posteo:", post_content, height=300)

            # Pregunta al usuario
            is_correct = st.radio("¿El contenido extraído es correcto?", ("Sí", "No"), index=0)
            if st.button("Confirmar Validación"):
                if is_correct == "Sí":
                    st.success("¡Gracias! El contenido ha sido validado correctamente.")
                else:
                    st.warning("Lamentablemente la app no logra recuperar automáticamente el contenido, lo revisaremos manualmente.")   
              
        except Exception as e:
            st.error(f"Hubo un error al intentar hacer web scraping: {e}")

        finally:
            # Guardar los resultados en el CSV
             df = pd.read_csv(csv_file)
             new_data = {
                 "ID": len(df) + 1,
                 "URL": url,
                 "Título": page_title,
                 "Contenido": post_content,
                 "Correcto": is_correct,
            }
            df = df.append(new_data, ignore_index=True)
            df.to_csv(csv_file, index=False)
            
            # Cerrar el navegador
            if "driver" in locals():
                driver.quit()

# Mostrar revisiones existentes
st.subheader("Revisiones Guardadas")
if os.path.exists(csv_file):
    df = pd.read_csv(csv_file)
    st.dataframe(df)
else:
    st.write("No hay revisiones guardadas todavía.")
