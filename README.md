# Gestor de Repositorio Git (PySide6 + PyGit2)

Una aplicación gráfica (GUI) moderna, ultra rápida y ligera desarrollada en Python utilizando **PySide6 (Qt 6)** y **PyGit2 (libgit2)** para gestionar repositorios Git de forma visual y de alto rendimiento.

---

## ⚡ Cambios Técnicos y Arquitectura

- **Motor Git Ultra Rápido (`PyGit2`):** Utiliza las vinculaciones nativas en C de `libgit2` para leer objetos, commits, estados y calcular diffs directamente en memoria sin cuellos de botella por creación de subprocesos en Windows.
- **Interfaz Gráfica Moderna (`PySide6`):** Desarrollada sobre Qt 6 con estilo oscuro *Fusion*, fuentes legibles de 14pt en listados y panel de vista previa con resaltado de sintaxis (`QSyntaxHighlighter`).
- **Estructuración de Datos sin Duplicados:** Salida limpia que discrimina claramente entre el **Título/Mensaje** del commit (1ª línea) y la **Descripción detallada** (a partir de la 3ª línea) en la consulta de historial y cambios.
- **Respaldo de Versión Anterior:** La versión previa basada en `CustomTkinter` se encuentra guardada como respaldo en la carpeta `backup_customtkinter/`.

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

Ejecuta en tu terminal:

```bash
pip install -r requirements.txt
```

O instala las librerías manualmente con `pip`:

```bash
pip install PySide6 pygit2 pillow
```

---

## 💻 Uso de la Aplicación

Ejecuta el archivo principal:

```bash
python main.py
```

---

## 📦 Compilación Optimizada para Arranque Ultra Rápido (.exe)

Para obtener un arranque instantáneo (en lugar del retraso de descomprimir archivos temporales con `--onefile`), la aplicación está configurada para compilarse en modo carpeta de distribución (`--onedir`) excluyendo los módulos innecesarios de PySide6 (como QtWebEngine, Qt3D, QtQuick, etc.).

Para compilar la aplicación, instala `pyinstaller` y ejecuta:

```bash
python -m PyInstaller --noconfirm main.spec
```

El ejecutable optimizado y sus librerías asociadas se crearán en la carpeta `dist/GestorGitGUI/GestorGitGUI.exe`.

> **Nota:** Al usar el ejecutable, se mostrará una pantalla de carga (*Splash Screen*) mientras se inicializa la aplicación.

---

## 🧪 Pruebas Unitarias

Para ejecutar las pruebas automáticas del servicio de Git:

```bash
python -m unittest test_git_service.py
```
