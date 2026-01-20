import os
import pyperclip
from tkinter import filedialog, Tk
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, RadioSet, RadioButton, Static, Label, ProgressBar
from textual.containers import Vertical, Horizontal, Center
from textual.screen import ModalScreen
from textual import work
import yt_dlp

# Estética mejorada
CSS = """
Screen {
    align: center middle;
}

#main-container {
    width: 65;
    height: auto;
    border: solid green;
    padding: 1 2;
    background: #242424;
}

/* Estilos para la pantalla de Ayuda */
HelpScreen {
    align: center middle;
}

#help-dialog {
    width: 50;
    height: auto;
    background: #1a1a1a;
    border: double cyan;
    padding: 1 2;
}

#help-text {
    margin-bottom: 1;
}

.help-title {
    text-align: center;
    text-style: bold;
    color: cyan;
    margin-bottom: 1;
}

Label {
    margin-top: 1;
    text-style: bold;
}

Input {
    margin-bottom: 1;
}

RadioSet {
    background: transparent;
    border: none;
    margin-bottom: 1;
}

.buttons-row {
    height: auto;
    align: center middle;
    margin-top: 1;
}

Button {
    width: 25;
    margin: 0 1;
}

ProgressBar {
    width: 85%;
    margin: 1 0;
    height: 3;
    align-horizontal: center;
}

ProgressBar > .progress-bar--percentage {
    width: 100%;
    text-align: center;
    color: $accent;
    text-style: bold;
}

ProgressBar > .progress-bar--bar {
    color: #00FF00;
    background: #222;
}

#status {
    margin-top: 1;
    text-align: center;
    width: 100%;
    color: yellow;
}
"""

# --- CLASE DE AYUDA ---
class HelpScreen(ModalScreen):
    """Pantalla emergente con información de ayuda."""
    
    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Label("--- INFORMACIÓN ---", classes="help-title")
            yield Static(
                "Version: 1.0\n"
                "Desarrollado por: shikaguero\n\n"
                "DESCRIPCIÓN:\n"
                "Herramienta TUI para descargar contenido de YouTube\n"
                "de forma rápida con calidad ajustable.\n\n"
                "FUNCIONAMIENTO:\n"
                "• [P] Pegar: Inserta link del portapapeles.\n"
                "• [L] Limpiar: Borra el link actual.\n"
                "• [D] Destino: Elige carpeta de guardado.\n"
                "• [S] Descargar: Inicia la conversión.\n\n"
                "Pulsa la Tecla ENTER para volver\n\n"
                "Visita mi perfil:\n"
                "https://github.com/shikaguero",
                id="help-text"
            )
            with Center():
                yield Button("Cerrar", variant="primary", id="close_help")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_help":
            self.app.pop_screen()

# --- CLASE PRINCIPAL ---
class YoutubTUI(App):
    CSS = CSS
    TITLE = "YouTube TUI Downloader"
    
    
    BINDINGS = [
        ("p", "pegar", "Pegar"),
        ("l", "limpiar", "Limpiar"),
        ("d", "destino", "Ruta"),
        ("s", "convertir", "Descargar"),
        ("a", "help", "Ayuda"),
        ("q", "quit", "Salir"),
    ]

    def __init__(self):
        super().__init__()
        self.save_path = os.getcwd()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-container"):
            yield Label("Enlace de YouTube:")
            yield Input(placeholder="Pega el link aquí (P)...", id="url_input")
            
            yield Label("Formato y Calidad:")
            with RadioSet(id="format_choice"):
                yield RadioButton("Audio (MP3)", id="mp3", value=True)
                yield RadioButton("Video MP4 (Low 720p)", id="mp4_low")
                yield RadioButton("Video MP4 (High 1080p)", id="mp4_high")
            
            with Horizontal(classes="buttons-row"):
                yield Button("Pegar (P)", variant="primary", id="btn_paste")
                yield Button("Limpiar (L)", variant="warning", id="btn_clear")
            
            with Horizontal(classes="buttons-row"):
                yield Button("Destino (D)", variant="default", id="btn_folder")
                yield Button("Descargar! (S)", variant="success", id="btn_convert")
            
            with Center(classes="buttons-row"):
                yield Button("Salir (Q)", variant="error", id="btn_exit")
            
            yield ProgressBar(id="progress-bar", total=100, show_percentage=True)
            yield Static("Listo", id="status")
        yield Footer()

    # --- Acciones ---
    def action_help(self):
        """Muestra la pantalla de ayuda."""
        self.push_screen(HelpScreen())

    def action_pegar(self): self.btn_paste_logic()
    def action_limpiar(self): self.btn_clear_logic()
    def action_destino(self): self.btn_folder_logic()
    def action_convertir(self): self.process_download()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_exit": self.exit()
        elif event.button.id == "btn_clear": self.btn_clear_logic()
        elif event.button.id == "btn_paste": self.btn_paste_logic()
        elif event.button.id == "btn_folder": self.btn_folder_logic()
        elif event.button.id == "btn_convert": self.process_download()

    def btn_clear_logic(self):
        self.query_one("#url_input", Input).value = ""
        self.query_one("#status").update("Input limpiado")

    def btn_paste_logic(self):
        self.query_one("#url_input", Input).value = pyperclip.paste()
        self.query_one("#status").update("Enlace pegado")

    def btn_folder_logic(self):
        root = Tk()
        root.withdraw()
        path = filedialog.askdirectory()
        root.destroy()
        if path:
            self.save_path = path
            self.query_one("#status").update(f"Carpeta: {os.path.basename(path)}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%','').strip()
            try:
                self.query_one("#progress-bar").progress = float(p)
            except ValueError:
                pass

    @work(thread=True, exclusive=True)
    def process_download(self) -> None:
        url = self.query_one("#url_input", Input).value
        format_id = self.query_one("#format_choice", RadioSet).pressed_button.id
        status = self.query_one("#status")
        bar = self.query_one("#progress-bar")

        if not url:
            status.update("[red]Error: Inserta un enlace[/red]")
            return

        bar.styles.display = "block"
        bar.progress = 0
        status.update("🔍 Analizando video...")

        ydl_opts = {
            'outtmpl': f'{self.save_path}/%(title)s.%(ext)s',
            'progress_hooks': [self.progress_hook],
            'quiet': True,
            'no_warnings': True,
        }

        if format_id == "mp3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif format_id == "mp4_low":
            ydl_opts.update({'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'})
        elif format_id == "mp4_high":
            ydl_opts.update({'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'})

        try:
            status.update("⏳ Descargando...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url]) 
            
            status.update("✅ ¡Descarga completada con éxito!")
            bar.progress = 100
        except Exception as e:
            status.update(f"[red]Error crítico: {str(e)[:50]}...[/red]")

if __name__ == "__main__":
    app = YoutubTUI()
    app.run()