import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# Título de la App
st.title("Validación de Contenidos de Redes Sociales (Selenium)")

# Ingreso de URL
st.subheader("Paso 1: Ingresar URL")
url = st.text_input("Ingresa la URL del posteo de la red social:")

if url:
    if st.button("Procesar URL"):
        try:
            # Configuración de Selenium para Modo Headless
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # Configurar ChromeDriver
            try:
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()), 
                    options=options
            )
            except Exception as e:
                st.error(f"Error al iniciar Selenium: {e}")
            
            # Abrir la URL
            driver.get(url)
            time.sleep(3)  # Esperar que la página cargue

            # Extraer contenido relevante (parárafos)
            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            page_content = " ".join([p.text for p in paragraphs if p.text.strip()])

            # Extraer título de la página
            page_title = driver.title

            # Cerrar Selenium
            driver.quit()

            # Mostrar resultados
            st.subheader("Paso 2: Resultado del Web Scraping")
            st.write(f"**Título de la Página:** {page_title}")
            st.text_area("Contenido Extraído:", page_content, height=300)

            # Validación del Usuario
            st.subheader("Paso 3: Validar el Contenido Extraído")
            is_correct = st.radio(
                "¿El contenido extraído es correcto?",
                ("Sí", "No"),
                index=0,
            )
            if st.button("Confirmar Validación"):
                if is_correct == "Sí":
                    st.success("¡Gracias! El contenido ha sido validado correctamente.")
                else:
                    st.warning("Por favor, verifica la URL o el contenido extraído.")

        except Exception as e:
            st.error(f"Hubo un error al intentar hacer web scraping: {e}")
