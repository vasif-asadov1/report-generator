# Report Generator Pro

Report Generator Pro is an offline, zero-latency Markdown and LaTeX note-taking environment optimized for Data Scientists and Analytics Professionals. Designed for speed, it allows you to compose complex technical reports using Markdown and LaTeX, with live rendering into a paginated slide view.

## Core Features
* **Zero-Latency Preview:** Instant rendering of Markdown and LaTeX equations without needing external server connections.
* **Intelligent Paginator:** Automatically slices your long notes into professional, floating page slides that mimic the look of a slide deck or word processor.
* **Professional Layout Engine:** Choose from standard formats (A4, A5, Letter) or create custom dimensions, perfectly scaled for reports or social media carousels (LinkedIn 1:1 / 4:5).
* **Automated Formatting:** Dynamic header colorization that adapts to your chosen UI theme or allows for manual color overrides.
* **Data-Driven Logging:** Built on SQLite to maintain a discrete history of your document progress, enabling you to manage your draft evolution log-by-log.
* **WYSIWYG Scaling:** Precise mathematical conversion from pixels to typographical points ensures that what you see in the preview is identical to your final exported PDF.
* **Code Highlighting:** Integrated support for multiple code syntax themes (Dracula, Solarized, GitHub, Catppuccin, etc.) for beautiful technical documentation.

## Installation Instructions

1. **Clone the Repository**: Download the project source code from GitHub to your local machine.
2. **Setup Python Environment**: Ensure you have Python 3.11 installed. It is highly recommended to use a virtual environment.
3. **Install Dependencies**: Open your terminal in the project root directory and run the command to install the required packages: `pip install PySide6 markdown pygments jinja2`.
4. **Execution**: Navigate into the source directory and run `python main.py` to launch the application.

## Usage Guide

* **Project Management**: Every project is treated as a single session. Use the "New" button to select a project folder. The app will generate a `.session` directory to store your database. Always use the "Open" button to resume work on an existing project database.
* **Writing**: Compose your notes in the left editor panel.
* **Previewing**: 
    * Press `Ctrl+S` to perform a live draft preview.
    * Press `Ctrl+Shift+S` to commit your current text as a permanent log in your document history.
* **Layout & Export**: 
    * Click the "Layout" button to change paper dimensions, theme colors, and font settings.
    * Click "Export" or press `Ctrl+Shift+E` to generate your final, perfectly formatted PDF.
* **Zooming**: Use `Ctrl` + `Mouse Wheel` to adjust the editor text size, or `Ctrl++` / `Ctrl+-` for keyboard-based scaling.

## Technology Stack

* **GUI Framework**: PySide6 (Qt for Python)
* **Rendering Engine**: QtWebEngine
* **Markdown Processing**: Python Markdown library with LaTeX support via MathJax
* **Code Highlighting**: Pygments
* **Data Persistence**: SQLite

## Roadmap & Support

This project is open-source. For feature requests, bug reports, or to contribute to the engine, please visit the official GitHub repository.

---
*Built for Data Professionals, by Data Professionals.*