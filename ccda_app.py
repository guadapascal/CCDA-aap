import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

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
                post_content = driver.find_element("xpath", "/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/section/main/div[2]/div[1]/article/div/div[2]/div/div[2]/div[1]/ul/div[1]/li/div/div/div[2]/div[1]").text
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
                    st.warning("Por favor, verifica la URL o el contenido extraído.")

        except Exception as e:
            st.error(f"Hubo un error al intentar hacer web scraping: {e}")

        finally:
            # Cerrar el navegador
            if "driver" in locals():
                driver.quit()
