import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# Función para inicializar el navegador Selenium
@st.cache_resource
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

# Título de la app
st.title("Validación de Contenidos de Redes Sociales")

# Entrada de URL por el usuario
url = st.text_input("Ingresa la URL del posteo de la red social:")

if url:
    if st.button("Procesar URL"):
        try:
            # Inicializar el navegador y cargar la URL
            driver = get_driver()
            driver.get(url)

            # Extraer título y contenido
            page_title = driver.title  # Título de la página
            page_content = driver.find_element("tag name", "body").text  # Contenido del cuerpo

            # Mostrar los resultados
            st.subheader("Resultado del Web Scraping")
            st.write(f"**Título de la Página:** {page_title}")
            st.text_area("Contenido Extraído:", page_content[:1000], height=300)

            # Preguntar al usuario si el scraping es correcto
            is_correct = st.radio("¿El contenido extraído es correcto?", ("Sí", "No"), index=0)
            if st.button("Confirmar Validación"):
                if is_correct == "Sí":
                    st.success("¡Gracias! El contenido ha sido validado correctamente.")
                else:
                    st.warning("Por favor, verifica la URL o el contenido extraído.")

             # Cerrar el navegador siempre
            if "driver" in locals():
            driver.quit()

        except Exception as e:
            st.error(f"Hubo un error al intentar hacer web scraping: {e}")
