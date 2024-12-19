{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/guadapascal/CCDA-aap/blob/main/ccda_app.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "Cmd9_7IUN_8P"
      },
      "source": [
        "# Critical and collaborative discourse analysis"
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "%%writefile ccdaapp-se3.py\n",
        "\n",
        "import streamlit as st\n",
        "from selenium import webdriver\n",
        "from selenium.webdriver.chrome.service import Service\n",
        "from selenium.webdriver.chrome.options import Options\n",
        "from webdriver_manager.chrome import ChromeDriverManager\n",
        "import time\n",
        "\n",
        "st.title(\"Validación de Contenidos de Redes Sociales (Selenium3)\")\n",
        "\n",
        "url = st.text_input(\"Ingresa la URL del posteo de la red social:\", \"\")\n",
        "\n",
        "if url:\n",
        "    try:\n",
        "        # Configuración de Selenium con WebDriver Manager\n",
        "        options = Options()\n",
        "        options.add_argument('--headless')\n",
        "        options.add_argument('--no-sandbox')\n",
        "        options.add_argument('--disable-dev-shm-usage')\n",
        "\n",
        "        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)\n",
        "\n",
        "        # Abrir la URL\n",
        "        driver.get(url)\n",
        "        time.sleep(3)  # Esperar que se cargue el contenido dinámico\n",
        "\n",
        "        # Extraer contenido\n",
        "        paragraphs = driver.find_elements(By.TAG_NAME, \"p\")\n",
        "        page_content = \" \".join([p.text for p in paragraphs if p.text.strip()])\n",
        "        page_title = driver.title\n",
        "\n",
        "        driver.quit()\n",
        "\n",
        "        st.subheader(\"Resultado del Web Scraping\")\n",
        "        st.write(f\"**Título de la Página:** {page_title}\")\n",
        "        st.text_area(\"Contenido Extraído:\", page_content, height=300)\n",
        "\n",
        "    except Exception as e:\n",
        "        st.error(f\"Hubo un error al intentar hacer web scraping: {e}\")\n"
      ],
      "metadata": {
        "colab": {
          "base_uri": "https://localhost:8080/"
        },
        "id": "0a-v1bru8POK",
        "outputId": "303d2ed5-b4b6-440e-c7a6-3e40480cd3f5"
      },
      "execution_count": 7,
      "outputs": [
        {
          "output_type": "stream",
          "name": "stdout",
          "text": [
            "Writing ccdaapp-se3.py\n"
          ]
        }
      ]
    }
  ],
  "metadata": {
    "colab": {
      "provenance": [],
      "gpuType": "T4",
      "authorship_tag": "ABX9TyNgru587c5aTqv70KFWX2QX",
      "include_colab_link": true
    },
    "kernelspec": {
      "display_name": "Python 3",
      "name": "python3"
    },
    "language_info": {
      "name": "python"
    },
    "accelerator": "GPU"
  },
  "nbformat": 4,
  "nbformat_minor": 0
}