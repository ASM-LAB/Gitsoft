# Gestor de Repositorio Git (Python CustomTkinter)

Una aplicación gráfica (GUI) moderna y sencilla desarrollada en Python utilizando **CustomTkinter** para gestionar repositorios Git de forma visual y rápida.

---

## 🚀 Características Principales

- **Selección de Repositorios:** Abre cualquier repositorio Git local y guarda el historial de repositorios recientes.
- **Área de Trabajo:**
  - Ver archivos modificados, no seguidos (*untracked*) y preparados (*staged*).
  - Preparar (*Stage*), Despreparar (*Unstage*) y Descartar cambios.
  - Añadir archivos no seguidos a `.gitignore` con un solo clic.
- **Creación de Commits en Formato Estándar:**
  - **Mensaje/Título:** Título corto o resumen del commit (1ª línea).
  - **Descripción Detallada:** Cuerpo o descripción explicativa (a partir de la 3ª línea, dejando la 2ª en blanco).
- **Historial de Commits:**
  - Visualiza los últimos commits ordenados por fecha, autor, mensaje y código hash.
  - Consulta los programas/archivos específicos afectados por cada commit.
- **Gestión de `.gitignore`:** Editor integrado para modificar directamente las reglas de ignorado.
- **Panel Lateral de Vista Previa (Diff):**
  - Muestra cambios y diffs en tiempo real con **resaltado de sintaxis** por colores (verde para adiciones `+`, rojo para eliminaciones `-`, cyan para cabeceras `@@`).
  - Formato en **negrita** para metadatos del commit (`Commit`, `Autor`, `Fecha`, `Mensaje`, `Descripción`).

---

## 🛠️ Requisitos e Instalación

### Requisitos Previos
- **Python 3.10+**
- **Git** instalado en el sistema.

### Instalación de Dependencias

Clona o descarga este repositorio y ejecuta:

```bash
pip install -r requirements.txt
```

O instala las librerías manualmente:

```bash
pip install customtkinter pillow
```

---

## 💻 Uso de la Aplicación

Ejecuta el archivo principal:

```bash
python main.py
```

### Flujo de trabajo rápido:
1. Haz clic en **Abrir Repositorio** o selecciona uno reciente en el desplegable superior.
2. En la pestaña **Área de Trabajo**, selecciona los archivos modificados y presiona **Preparar (Stage)**.
3. Ingresa el **Mensaje/Título** y la **Descripción detallada** en la sección inferior.
4. Presiona **Crear Commit**.
5. Revisa el resultado en la pestaña **Historial de Commits** y consulta el código modificado en el panel lateral de **Vista Previa (Diff)**.

---

## 🧪 Pruebas Unitarias

Para ejecutar las pruebas automáticas del servicio de Git:

```bash
python -m unittest test_git_service.py
```
