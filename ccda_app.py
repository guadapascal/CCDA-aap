import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Título de la app
st.title("Validación de Contenidos de Redes Sociales")

# Ingreso de URL
url = st.text_input("Ingresa la URL del posteo de la red social:")

if url:
    if st.button("Procesar URL"):
        try:
            # Configuración de Selenium con Chromium
            options = Options()
            options.add_argument('--headless')  # Modo sin interfaz gráfica
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # Especificar la ruta del navegador Chromium
            options.binary_location = '/usr/bin/chromium-browser'

            # Inicializar el controlador Chrome con Selenium
            driver = webdriver.Chrome(service=Service('/usr/bin/chromedriver'), options=options)

            # Abrir la URL
            driver.get(url)

            # Extraer contenido
            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            page_content = " ".join([p.text for p in paragraphs if p.text.strip()])
            page_title = driver.title

            # Cerrar el navegador
            driver.quit()

            # Mostrar resultados
            st.subheader("Resultado del Web Scraping")
            st.write(f"**Título de la Página:** {page_title}")
            st.text_area("Contenido Extraído:", page_content, height=300)

        except Exception as e:
            st.error(f"Hubo un error al intentar hacer web scraping: {e}")
