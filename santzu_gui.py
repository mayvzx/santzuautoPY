import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import threading
import os
from pynput import keyboard
from macro_recorder import MacroRecorder
from vision_utils import find_image_on_screen
import time
from config_manager import ConfigManager
from PIL import Image, ImageDraw # Importar Pillow para lidar com imagens
import sys # Importar sys aqui

# Configuração do tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class SantzuGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Santzu - A Arte da Automação")
        self.root.geometry("1000x900")
        self.root.configure(fg_color="#1A1A1A")
        
        self.config_manager = ConfigManager()
        self.macro_recorder = MacroRecorder(self.config_manager)
        
        self.is_recording = False
        self.current_macro_file = None
        
        self.repeat_mode = tk.StringVar(value="once")
        self.repeat_count = ctk.IntVar(value=1)
        
        self.macros_dir = self.config_manager.get_setting("macros_directory")
        if not os.path.exists(self.macros_dir):
            os.makedirs(self.macros_dir)
        
        # Carregar o ícone de status original (preto e branco ou com transparência)
        self.original_status_icon = Image.open(resource_path("santzu_status_icon.png")).convert("RGBA")
        self.status_icon_size = (20, 20)

        self.setup_ui()
        self.setup_hotkeys()
        self.refresh_macro_list()

        self.hotkey_capture_listener = None
        self.hotkey_entry_to_update = None

        # Indicador visual de status (agora usando o ícone)
        self.status_indicator = ctk.CTkLabel(
            self.root,
            text="",
            image=None, # A imagem será definida pela função update_status_indicator
            compound="left", 
            fg_color="transparent"
        )
        self.status_indicator.place(x=10, y=10) # Posição no canto superior esquerdo
        self.update_status_indicator("gray") # Define a cor inicial
        
    def setup_ui(self):
        main_frame = ctk.CTkScrollableFrame(self.root, fg_color="#1A1A1A")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame, 
            text="孫子 SANTZU 孫子",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#DAA520"
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="A Arte da Guerra na Automação",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#CC0000"
        )
        subtitle_label.pack(pady=(0, 30))
        
        controls_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        controls_frame.pack(fill="x", pady=(0, 20))
        
        buttons_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        self.record_button = ctk.CTkButton(
            buttons_frame,
            text="🔴 INICIAR GRAVAÇÃO (F9)",
            command=self.toggle_recording,
            width=200,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#CC0000",
            hover_color="#AA0000"
        )
        self.record_button.pack(side="left", padx=10)
        
        self.play_button = ctk.CTkButton(
            buttons_frame,
            text="▶️ EXECUTAR MACRO (F10)",
            command=self.play_macro,
            width=200,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#DAA520",
            hover_color="#B8860B"
        )
        self.play_button.pack(side="left", padx=10)

        settings_button = ctk.CTkButton(
            buttons_frame,
            text="⚙️ Configurações",
            command=self.open_settings_window,
            width=150,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#555555",
            hover_color="#666666"
        )
        settings_button.pack(side="left", padx=10)
        
        macro_management_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        macro_management_frame.pack(fill="x", pady=(0, 20))
        
        macro_mgmt_label = ctk.CTkLabel(
            macro_management_frame,
            text="Gerenciamento de Macros",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#DAA520"
        )
        macro_mgmt_label.pack(pady=(10, 5))
        
        macro_content_frame = ctk.CTkFrame(macro_management_frame, fg_color="transparent")
        macro_content_frame.pack(fill="x", padx=20, pady=10)
        
        macro_list_frame = ctk.CTkFrame(macro_content_frame, fg_color="#2B2B2B")
        macro_list_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        list_label = ctk.CTkLabel(
            macro_list_frame,
            text="Macros Disponíveis",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#DAA520"
        )
        list_label.pack(pady=(10, 5))
        
        self.macro_listbox = tk.Listbox(
            macro_list_frame,
            bg="#1A1A1A",
            fg="#F0F0F0",
            selectbackground="#DAA520",
            selectforeground="#000000",
            font=("Arial", 10),
            height=8
        )
        self.macro_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        macro_controls_frame = ctk.CTkFrame(macro_content_frame, fg_color="#2B2B2B")
        macro_controls_frame.pack(side="right", fill="y", padx=(10, 0))
        
        controls_label = ctk.CTkLabel(
            macro_controls_frame,
            text="Controles",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#DAA520"
        )
        controls_label.pack(pady=(10, 15))
        
        load_selected_button = ctk.CTkButton(
            macro_controls_frame,
            text="📂 Carregar\nSelecionada",
            command=self.load_selected_macro,
            width=120,
            height=50,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#555555",
            hover_color="#666666"
        )
        load_selected_button.pack(pady=5)
        
        save_new_button = ctk.CTkButton(
            macro_controls_frame,
            text="💾 Salvar\nNova",
            command=self.save_new_macro,
            width=120,
            height=50,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#555555",
            hover_color="#666666"
        )
        save_new_button.pack(pady=5)
        
        rename_button = ctk.CTkButton(
            macro_controls_frame,
            text="✏️ Renomear",
            command=self.rename_selected_macro,
            width=120,
            height=40,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#555555",
            hover_color="#666666"
        )
        rename_button.pack(pady=5)
        
        delete_button = ctk.CTkButton(
            macro_controls_frame,
            text="🗑️ Excluir",
            command=self.delete_selected_macro,
            width=120,
            height=40,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#AA0000",
            hover_color="#880000"
        )
        delete_button.pack(pady=5)
        
        refresh_button = ctk.CTkButton(
            macro_controls_frame,
            text="🔄 Atualizar",
            command=self.refresh_macro_list,
            width=120,
            height=40,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#555555",
            hover_color="#666666"
        )
        refresh_button.pack(pady=5)
        
        strategic_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        strategic_frame.pack(fill="x", pady=(0, 20))

        strategic_label = ctk.CTkLabel(
            strategic_frame,
            text="Modo de Reprodução Estratégica",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#DAA520"
        )
        strategic_label.pack(pady=(10, 5))

        self.condition_entry = ctk.CTkEntry(
            strategic_frame,
            placeholder_text="Ex: 'se imagem.png aparecer', 'se tempo > 5s'",
            width=400,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#1A1A1A",
            text_color="#F0F0F0"
        )
        self.condition_entry.pack(pady=10)

        add_condition_button = ctk.CTkButton(
            strategic_frame,
            text="➕ Adicionar Condição ao Próximo Evento Gravado",
            command=self.add_condition_to_next_event,
            width=250,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#555555",
            hover_color="#666666"
        )
        add_condition_button.pack(pady=(0, 10))
        
        repeat_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        repeat_frame.pack(fill="x", pady=(0, 20))

        repeat_label = ctk.CTkLabel(
            repeat_frame,
            text="Opções de Repetição",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#DAA520"
        )
        repeat_label.pack(pady=(10, 5))

        repeat_options_frame = ctk.CTkFrame(repeat_frame, fg_color="transparent")
        repeat_options_frame.pack(pady=10)

        once_radio = ctk.CTkRadioButton(
            repeat_options_frame,
            text="Reproduzir uma vez",
            variable=self.repeat_mode,
            value="once",
            text_color="#F0F0F0",
            fg_color="#DAA520"
        )
        once_radio.pack(side="left", padx=10)

        continuous_radio = ctk.CTkRadioButton(
            repeat_options_frame,
            text="Reproduzir indefinidamente",
            variable=self.repeat_mode,
            value="continuous",
            text_color="#F0F0F0",
            fg_color="#DAA520"
        )
        continuous_radio.pack(side="left", padx=10)

        repeat_count_frame = ctk.CTkFrame(repeat_options_frame, fg_color="transparent")
        repeat_count_frame.pack(side="left", padx=10)

        repeat_count_radio = ctk.CTkRadioButton(
            repeat_count_frame,
            text="Repetir",
            variable=self.repeat_mode,
            value="repeat_count",
            text_color="#F0F0F0",
            fg_color="#DAA520"
        )
        repeat_count_radio.pack(side="left")

        self.repeat_count_entry = ctk.CTkEntry(
            repeat_count_frame,
            textvariable=self.repeat_count,
            width=50,
            height=25,
            font=ctk.CTkFont(size=12),
            fg_color="#1A1A1A",
            text_color="#F0F0F0"
        )
        self.repeat_count_entry.pack(side="left", padx=5)

        ctk.CTkLabel(
            repeat_count_frame,
            text="vezes",
            text_color="#F0F0F0"
        ).pack(side="left")

        # Contador de repetições
        self.current_repetition_label = ctk.CTkLabel(
            repeat_count_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#DAA520"
        )
        self.current_repetition_label.pack(side="left", padx=10)
        
        status_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        status_frame.pack(fill="both", expand=True)
        
        status_label = ctk.CTkLabel(
            status_frame,
            text="Status do Sistema",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#DAA520"
        )
        status_label.pack(pady=(10, 5))
        
        self.status_text = ctk.CTkTextbox(
            status_frame,
            width=700,
            height=120,
            font=ctk.CTkFont(size=12),
            fg_color="#1A1A1A",
            text_color="#F0F0F0"
        )
        self.status_text.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.update_status("Santzu iniciado. Pronto para a batalha da automação.")
        self.update_status("\"Conheça seu inimigo e conheça a si mesmo\" - Sun Tzu")
        
        quote_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        quote_frame.pack(fill="x", pady=(10, 0))
        
        self.quote_label = ctk.CTkLabel(
            quote_frame,
            text="\"A suprema excelência consiste em quebrar a resistência do inimigo sem lutar.\"",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#DAA520",
            wraplength=700
        )
        self.quote_label.pack(pady=10)
        
    def setup_hotkeys(self):
        if hasattr(self, 'hotkey_listener') and self.hotkey_listener.running:
            self.hotkey_listener.stop()
            self.hotkey_listener.join()

        record_hotkey = self.config_manager.get_setting('hotkeys.record_toggle')
        play_hotkey = self.config_manager.get_setting('hotkeys.play_toggle')
        pause_hotkey = self.config_manager.get_setting('hotkeys.pause_toggle')

        def on_record_toggle():
            self.root.after(0, self.toggle_recording)

        def on_play_toggle():
            self.root.after(0, self.play_macro)

        def on_pause_toggle():
            self.root.after(0, self.toggle_pause_play)

        self.hotkey_listener = keyboard.GlobalHotKeys({
            record_hotkey: on_record_toggle,
            play_hotkey: on_play_toggle,
            pause_hotkey: on_pause_toggle
        })
        self.hotkey_listener.start()
        self.update_status(f"Hotkeys ativadas: Gravar/Parar ({self.format_hotkey_display(record_hotkey)}), Reproduzir ({self.format_hotkey_display(play_hotkey)}), Pausar/Retomar ({self.format_hotkey_display(pause_hotkey)}).")
        self.update_main_button_hotkeys()

    def format_hotkey_display(self, hotkey_str):
        # Remove '<' e '>' e 'Key.' e converte para maiúsculas
        formatted_key = hotkey_str.replace("<", "").replace(">", "").replace("Key.", "").upper()
        # Trata casos especiais como 'space' para 'SPACE' ou 'enter' para 'ENTER'
        if formatted_key == 'SPACE':
            return 'Espaço'
        elif formatted_key == 'ENTER':
            return 'Enter'
        elif formatted_key == 'ESC':
            return 'Esc'
        return formatted_key

    def update_main_button_hotkeys(self):
        record_hotkey = self.config_manager.get_setting('hotkeys.record_toggle')
        play_hotkey = self.config_manager.get_setting('hotkeys.play_toggle')
        self.record_button.configure(text=f"🔴 INICIAR GRAVAÇÃO ({self.format_hotkey_display(record_hotkey)})")
        self.play_button.configure(text=f"▶️ EXECUTAR MACRO ({self.format_hotkey_display(play_hotkey)})")

    def update_status(self, message):
        self.status_text.insert("end", f"{message}\n")
        self.status_text.see("end")
        
    def refresh_macro_list(self):
        self.macro_listbox.delete(0, tk.END)
        
        if os.path.exists(self.macros_dir):
            for filename in os.listdir(self.macros_dir):
                if filename.endswith(".json"):
                    display_name = filename[:-5]
                    self.macro_listbox.insert(tk.END, display_name)
        
        self.update_status(f"Lista de macros atualizada. {self.macro_listbox.size()} macros encontradas.")
    
    def load_selected_macro(self):
        selection = self.macro_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma macro da lista.")
            return
        
        selected_name = self.macro_listbox.get(selection[0])
        filename = os.path.join(self.macros_dir, f"{selected_name}.json")
        
        try:
            self.macro_recorder.load_macro(filename)
            self.current_macro_file = filename
            self.update_status(f"📂 Macro '{selected_name}' carregada com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar macro: {str(e)}")
    
    def save_new_macro(self):
        if not self.macro_recorder.events:
            messagebox.showwarning("Aviso", "Nenhuma macro para salvar.")
            return
        
        dialog = ctk.CTkInputDialog(
            text="Digite o nome da nova macro:",
            title="Salvar Nova Macro"
        )
        macro_name = dialog.get_input()
        
        if macro_name:
            safe_name = "".join(c for c in macro_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = os.path.join(self.macros_dir, f"{safe_name}.json")
            
            try:
                self.macro_recorder.save_macro(filename)
                self.current_macro_file = filename
                self.refresh_macro_list()
                self.update_status(f"💾 Macro '{safe_name}' salva com sucesso.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar macro: {str(e)}")
    
    def rename_selected_macro(self):
        selection = self.macro_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma macro da lista.")
            return
        
        old_name = self.macro_listbox.get(selection[0])
        old_filename = os.path.join(self.macros_dir, f"{old_name}.json")
        
        dialog = ctk.CTkInputDialog(
            text=f"Digite o novo nome para '{old_name}':",
            title="Renomear Macro"
        )
        new_name = dialog.get_input()
        
        if new_name:
            safe_name = "".join(c for c in new_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            new_filename = os.path.join(self.macros_dir, f"{safe_name}.json")
            
            try:
                os.rename(old_filename, new_filename)
                self.refresh_macro_list()
                self.update_status(f"✏️ Macro renomeada de '{old_name}' para '{safe_name}'.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao renomear macro: {str(e)}")
    
    def delete_selected_macro(self):
        selection = self.macro_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma macro da lista.")
            return
        
        selected_name = self.macro_listbox.get(selection[0])
        filename = os.path.join(self.macros_dir, f"{selected_name}.json")
        
        result = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a macro '{selected_name}'?\n\nEsta ação não pode ser desfeita."
        )
        
        if result:
            try:
                os.remove(filename)
                self.refresh_macro_list()
                self.update_status(f"🗑️ Macro '{selected_name}' excluída com sucesso.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir macro: {str(e)}")
    
    def toggle_recording(self):
        if self.macro_recorder.playing:
            messagebox.showwarning("Aviso", "Não é possível iniciar a gravação enquanto uma macro está sendo reproduzida.")
            return

        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        if self.macro_recorder.recording: # Evita iniciar gravação se já estiver gravando
            return
        self.is_recording = True
        self.record_button.configure(
            text="⏹️ PARAR GRAVAÇÃO (F9)",
            fg_color="#AA0000"
        )
        self.macro_recorder.start_recording()
        self.update_status("🔴 Gravação iniciada. Todas as ações estão sendo capturadas.")
        self.update_status_indicator("red") # Indicador visual de gravação
        
    def stop_recording(self):
        if not self.macro_recorder.recording: # Evita parar gravação se não estiver gravando
            return
        self.is_recording = False
        self.record_button.configure(
            text="🔴 INICIAR GRAVAÇÃO (F9)",
            fg_color="#CC0000"
        )
        self.macro_recorder.stop_recording()
        self.update_status("⏹️ Gravação parada. Macro pronta para execução.")
        self.update_status_indicator("gray") # Indicador visual neutro
        
    def play_macro(self):
        if self.macro_recorder.recording: # Trava: não pode iniciar reprodução se estiver gravando
            messagebox.showwarning("Aviso", "Não é possível iniciar a reprodução enquanto uma macro está sendo gravada.")
            return
        if self.macro_recorder.playing: # Trava: não pode iniciar reprodução se já estiver reproduzindo
            messagebox.showwarning("Aviso", "Uma macro já está em reprodução.")
            return

        if not self.macro_recorder.events:
            messagebox.showwarning("Aviso", "Nenhuma macro gravada ou carregada.")
            return
            
        self.update_status("▶️ Executando macro...")
        self.update_status_indicator("blue") # Indicador visual de reprodução
        
        mode = self.repeat_mode.get()
        count = self.repeat_count.get() if mode == 'repeat_count' else 1

        # Desabilitar botões de controle durante a reprodução para evitar conflitos
        self.record_button.configure(state="disabled")
        self.play_button.configure(state="disabled")

        threading.Thread(target=self._play_macro_thread, args=(mode, count), daemon=True).start()
        
    def _play_macro_thread(self, mode, count):
        try:
            for i in range(1, count + 1):
                if mode == 'repeat_count' or mode == 'continuous':
                    self.root.after(0, lambda i=i, count=count: self.current_repetition_label.configure(text=f"Repetição: {i}/{count}" if mode == 'repeat_count' else f"Repetição: {i}"))
                self.macro_recorder.play_macro(
                    evaluate_conditions_callback=self.evaluate_condition,
                    repeat_mode=mode,
                    repeat_count=count
                )
            self.root.after(0, lambda: self.update_status("✅ Macro executada com sucesso."))
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"❌ Erro ao executar macro: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.update_status_indicator("gray")) # Indicador visual neutro
            self.root.after(0, lambda: self.current_repetition_label.configure(text=""))
            # Reabilitar botões de controle após a reprodução
            self.root.after(0, lambda: self.record_button.configure(state="normal"))
            self.root.after(0, lambda: self.play_button.configure(state="normal"))

    def add_condition_to_next_event(self):
        condition_text = self.condition_entry.get()
        if not condition_text:
            messagebox.showwarning("Aviso", "Por favor, insira uma condição no campo de texto.")
            return

        if not self.macro_recorder.events:
            messagebox.showwarning("Aviso", "Nenhum evento gravado para adicionar condição.")
            return

        self.macro_recorder.events[-1]["condition"] = condition_text
        self.update_status(f"Condição '{condition_text}' adicionada ao último evento gravado.")
        self.condition_entry.delete(0, ctk.END)

    def evaluate_condition(self, condition_str):
        self.update_status(f"Avaliando condição: {condition_str}")
        if condition_str.startswith("se imagem.png aparecer"):
            image_path = condition_str.split(" ")[-1]
            found = find_image_on_screen(image_path)
            if found:
                self.update_status(f"Condição 'imagem {image_path} aparecer' atendida.")
                return True
            else:
                self.update_status(f"Condição 'imagem {image_path} aparecer' NÃO atendida.")
                return False
        elif condition_str.startswith("se tempo > "):
            try:
                time_val = float(condition_str.split(" ")[-1].replace("s", ""))
                current_time_in_macro = time.time() - self.macro_recorder.start_time
                if current_time_in_macro > time_val:
                    self.update_status(f"Condição 'tempo > {time_val}s' atendida.")
                    return True
                else:
                    self.update_status(f"Condição 'tempo > {time_val}s' NÃO atendida.")
                    return False
            except ValueError:
                self.update_status(f"Erro ao avaliar condição de tempo: {condition_str}")
                return False
        else:
            self.update_status(f"Condição '{condition_str}' não reconhecida. Assumindo como verdadeira.")
            return True

    def open_settings_window(self):
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Configurações do Santzu")
        settings_window.geometry("600x550")
        settings_window.transient(self.root)
        settings_window.grab_set()

        settings_frame = ctk.CTkFrame(settings_window, fg_color="#2B2B2B")
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        settings_title = ctk.CTkLabel(
            settings_frame,
            text="Configurações",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#DAA520"
        ).pack(pady=(0, 20))

        hotkeys_frame = ctk.CTkFrame(settings_frame, fg_color="#333333")
        hotkeys_frame.pack(fill="x", pady=(0, 15), padx=10)

        ctk.CTkLabel(
            hotkeys_frame,
            text="Hotkeys",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#DAA520"
        ).pack(pady=(10, 5))

        # Hotkey Gravar/Parar
        record_hk_frame = ctk.CTkFrame(hotkeys_frame, fg_color="transparent")
        record_hk_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(record_hk_frame, text="Gravar/Parar:", text_color="#F0F0F0").pack(side="left", padx=(0, 10))
        self.record_hotkey_entry = ctk.CTkEntry(record_hk_frame, width=100, fg_color="#1A1A1A", text_color="#F0F0F0")
        self.record_hotkey_entry.insert(0, self.format_hotkey_display(self.config_manager.get_setting('hotkeys.record_toggle')))
        self.record_hotkey_entry.pack(side="left", expand=True, fill="x")
        record_capture_button = ctk.CTkButton(record_hk_frame, text="Capturar", command=lambda: self.start_hotkey_capture(self.record_hotkey_entry))
        record_capture_button.pack(side="left", padx=5)

        # Hotkey Reproduzir
        play_hk_frame = ctk.CTkFrame(hotkeys_frame, fg_color="transparent")
        play_hk_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(play_hk_frame, text="Reproduzir:", text_color="#F0F0F0").pack(side="left", padx=(0, 10))
        self.play_hotkey_entry = ctk.CTkEntry(play_hk_frame, width=100, fg_color="#1A1A1A", text_color="#F0F0F0")
        self.play_hotkey_entry.insert(0, self.format_hotkey_display(self.config_manager.get_setting('hotkeys.play_toggle')))
        self.play_hotkey_entry.pack(side="left", expand=True, fill="x")
        play_capture_button = ctk.CTkButton(play_hk_frame, text="Capturar", command=lambda: self.start_hotkey_capture(self.play_hotkey_entry))
        play_capture_button.pack(side="left", padx=5)

        # Hotkey Pausar/Retomar
        pause_hk_frame = ctk.CTkFrame(hotkeys_frame, fg_color="transparent")
        pause_hk_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(pause_hk_frame, text="Pausar/Retomar:", text_color="#F0F0F0").pack(side="left", padx=(0, 10))
        self.pause_hotkey_entry = ctk.CTkEntry(pause_hk_frame, width=100, fg_color="#1A1A1A", text_color="#F0F0F0")
        self.pause_hotkey_entry.insert(0, self.format_hotkey_display(self.config_manager.get_setting('hotkeys.pause_toggle')))
        self.pause_hotkey_entry.pack(side="left", expand=True, fill="x")
        pause_capture_button = ctk.CTkButton(pause_hk_frame, text="Capturar", command=lambda: self.start_hotkey_capture(self.pause_hotkey_entry))
        pause_capture_button.pack(side="left", padx=5)

        speed_frame = ctk.CTkFrame(settings_frame, fg_color="#333333")
        speed_frame.pack(fill="x", pady=(0, 15), padx=10)

        ctk.CTkLabel(
            speed_frame,
            text="Velocidade de Reprodução",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#DAA520"
        ).pack(pady=(10, 5))

        self.playback_speed_var = ctk.StringVar(value=self.config_manager.get_setting('playback_speed'))
        speed_options = ["normal", "slow", "fast", "custom"]
        self.playback_speed_optionmenu = ctk.CTkOptionMenu(
            speed_frame,
            values=speed_options,
            variable=self.playback_speed_var,
            command=self.update_custom_speed_entry_state
        )
        self.playback_speed_optionmenu.pack(pady=5)

        custom_speed_frame = ctk.CTkFrame(speed_frame, fg_color="transparent")
        custom_speed_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(custom_speed_frame, text="Multiplicador Customizado:", text_color="#F0F0F0").pack(side="left", padx=(0, 10))
        self.custom_speed_entry = ctk.CTkEntry(custom_speed_frame, width=80, fg_color="#1A1A1A", text_color="#F0F0F0")
        self.custom_speed_entry.insert(0, str(self.config_manager.get_setting('custom_playback_speed_multiplier')))
        self.custom_speed_entry.pack(side="left", expand=True, fill="x")
        self.update_custom_speed_entry_state(self.playback_speed_var.get())

        save_settings_button = ctk.CTkButton(
            settings_frame,
            text="Salvar Configurações",
            command=self.save_settings,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#DAA520",
            hover_color="#B8860B"
        ).pack(pady=20)

        settings_window.protocol("WM_DELETE_WINDOW", lambda: self.on_settings_close(settings_window))

    def update_custom_speed_entry_state(self, selected_speed):
        if selected_speed == "custom":
            self.custom_speed_entry.configure(state="normal")
        else:
            self.custom_speed_entry.configure(state="disabled")

    def save_settings(self):
        # Salva as hotkeys no formato original (com 'Key.' e '<>')
        self.config_manager.set_setting('hotkeys.record_toggle', self.get_hotkey_original_format(self.record_hotkey_entry.get()))
        self.config_manager.set_setting('hotkeys.play_toggle', self.get_hotkey_original_format(self.play_hotkey_entry.get()))
        self.config_manager.set_setting('hotkeys.pause_toggle', self.get_hotkey_original_format(self.pause_hotkey_entry.get()))

        self.config_manager.set_setting('playback_speed', self.playback_speed_var.get())
        try:
            custom_multiplier = float(self.custom_speed_entry.get())
            self.config_manager.set_setting('custom_playback_speed_multiplier', custom_multiplier)
        except ValueError:
            messagebox.showerror("Erro", "Multiplicador de velocidade customizado inválido. Use um número.")
            return

        self.config_manager.save_config()
        messagebox.showinfo("Configurações Salvas", "As configurações foram salvas com sucesso! As hotkeys serão atualizadas na próxima inicialização ou ao reiniciar o listener.")
        self.update_status("Configurações salvas. Reinicie o Santzu para aplicar as novas hotkeys.")
        self.setup_hotkeys()

    def get_hotkey_original_format(self, hotkey_display_str):
        # Converte de volta para o formato que pynput espera
        if hotkey_display_str.lower() == 'espaço':
            return 'Key.space'
        elif hotkey_display_str.lower() == 'enter':
            return 'Key.enter'
        elif hotkey_display_str.lower() == 'esc':
            return 'Key.esc'
        elif len(hotkey_display_str) == 1: # Caracteres únicos
            return hotkey_display_str.lower()
        else: # Teclas especiais como F1, F2, etc.
            return f"<Key.{hotkey_display_str.lower()}>"

    def on_settings_close(self, window):
        window.destroy()
        self.update_status("Janela de configurações fechada.")

    def toggle_pause_play(self):
        if self.macro_recorder.playing:
            if self.macro_recorder.paused:
                self.macro_recorder.resume_playing()
                self.update_status("▶️ Reprodução da macro retomada.")
            else:
                self.macro_recorder.pause_playing()
                self.update_status("⏸️ Reprodução da macro pausada.")
        else:
            messagebox.showwarning("Aviso", "Nenhuma macro está sendo reproduzida para pausar/retomar.")

    def start_hotkey_capture(self, entry_widget):
        self.hotkey_entry_to_update = entry_widget
        entry_widget.delete(0, ctk.END)
        entry_widget.insert(0, "Pressione uma tecla...")
        entry_widget.configure(state="disabled")

        if self.hotkey_capture_listener:
            self.hotkey_capture_listener.stop()
            self.hotkey_capture_listener.join()

        self.hotkey_capture_listener = keyboard.Listener(on_press=self.on_key_press_for_capture)
        self.hotkey_capture_listener.start()
        self.update_status("Aguardando nova hotkey...")

    def on_key_press_for_capture(self, key):
        try:
            key_str = str(key).replace("'", "")
            if key_str.startswith("Key."):
                key_str = key_str.split(".")[-1]
            
            self.root.after(0, lambda: self.update_hotkey_entry(key_str))
            return False
        except AttributeError:
            self.root.after(0, lambda: self.update_hotkey_entry(str(key)))
            return False

    def update_hotkey_entry(self, key_str):
        if self.hotkey_entry_to_update:
            self.hotkey_entry_to_update.configure(state="normal")
            self.hotkey_entry_to_update.delete(0, ctk.END)
            self.hotkey_entry_to_update.insert(0, self.format_hotkey_display(key_str))
            self.hotkey_entry_to_update = None
        if self.hotkey_capture_listener:
            self.hotkey_capture_listener.stop()
            self.hotkey_capture_listener.join()
            self.hotkey_capture_listener = None
        self.update_status(f"Hotkey capturada: {self.format_hotkey_display(key_str)}")

    def update_status_indicator(self, color):
        # Cria uma cópia da imagem original para não modificar a original
        colored_image = self.original_status_icon.copy()
        
        # Preenche as áreas não transparentes com a nova cor
        data = colored_image.getdata()
        new_data = []
        for item in data:
            # item é uma tupla (R, G, B, A)
            if item[3] != 0: # Se não for totalmente transparente
                new_data.append(ImageDraw.ImageColor.getrgb(color) + (item[3],)) # Mantém o canal alfa original
            else:
                new_data.append(item) # Mantém a transparência
        colored_image.putdata(new_data)

        # Redimensiona a imagem para o tamanho desejado
        colored_image = colored_image.resize(self.status_icon_size, Image.LANCZOS)
        
        # Atualiza a imagem do CTkLabel
        self.status_indicator.configure(image=ctk.CTkImage(colored_image, size=self.status_icon_size))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    import sys # Importar sys aqui
    app = SantzuGUI()
    app.run()

