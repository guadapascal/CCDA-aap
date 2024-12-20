import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

# Título de la app
st.title("Validación de Contenidos de Redes Sociales")

# Ingreso de URL
url = st.text_input("Ingresa la URL del posteo de la red social:")

if url:
    if st.button("Procesar URL"):
        try:
            # Configuración de undetected-chromedriver
            options = uc.ChromeOptions()
            options.add_argument('--headless')  # Ejecutar en modo sin interfaz gráfica
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # Inicializar el navegador con undetected-chromedriver
            driver = uc.Chrome(options=options)

            # Abrir la URL
            driver.get(url)

            # Extraer contenido
            paragraphs = driver.find_elements_by_tag_name("p")
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
