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

# Configuração do tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class SantzuGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Santzu - A Arte da Automação")
        self.root.geometry("1000x900") # Aumentar a largura e altura para acomodar nova funcionalidade
        self.root.configure(fg_color="#1A1A1A")
        
        # Inicializar o gravador de macro
        self.macro_recorder = MacroRecorder()
        
        # Variáveis de estado
        self.is_recording = False
        self.current_macro_file = None
        
        # Variáveis para opções de repetição
        self.repeat_mode = tk.StringVar(value="once") # 'once', 'continuous', 'repeat_count'
        self.repeat_count = ctk.IntVar(value=1)
        
        # Criar pasta de macros se não existir
        self.macros_dir = "macros"
        if not os.path.exists(self.macros_dir):
            os.makedirs(self.macros_dir)
        
        self.setup_ui()
        self.setup_hotkeys()
        self.refresh_macro_list()
        
    def setup_ui(self):
        # Frame principal com scroll
        main_frame = ctk.CTkScrollableFrame(self.root, fg_color="#1A1A1A")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título principal com estilo Sun Tzu
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
        
        # Frame de controles principais
        controls_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        controls_frame.pack(fill="x", pady=(0, 20))
        
        # Botões principais
        buttons_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        # Botão de gravação
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
        
        # Botão de reprodução
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
        
        # --- NOVO: Frame de Gerenciamento de Macros ---
        macro_management_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        macro_management_frame.pack(fill="x", pady=(0, 20))
        
        macro_mgmt_label = ctk.CTkLabel(
            macro_management_frame,
            text="Gerenciamento de Macros",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#DAA520"
        )
        macro_mgmt_label.pack(pady=(10, 5))
        
        # Frame horizontal para lista e controles
        macro_content_frame = ctk.CTkFrame(macro_management_frame, fg_color="transparent")
        macro_content_frame.pack(fill="x", padx=20, pady=10)
        
        # Frame esquerdo - Lista de macros
        macro_list_frame = ctk.CTkFrame(macro_content_frame, fg_color="#2B2B2B")
        macro_list_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        list_label = ctk.CTkLabel(
            macro_list_frame,
            text="Macros Disponíveis",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#DAA520"
        )
        list_label.pack(pady=(10, 5))
        
        # Lista de macros
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
        
        # Frame direito - Controles de macro
        macro_controls_frame = ctk.CTkFrame(macro_content_frame, fg_color="#2B2B2B")
        macro_controls_frame.pack(side="right", fill="y", padx=(10, 0))
        
        controls_label = ctk.CTkLabel(
            macro_controls_frame,
            text="Controles",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#DAA520"
        )
        controls_label.pack(pady=(10, 15))
        
        # Botões de controle
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
        
        # --- Fim do Frame de Gerenciamento de Macros ---
        
        # --- Frame para o Modo de Reprodução Estratégica ---
        strategic_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        strategic_frame.pack(fill="x", pady=(0, 20))

        strategic_label = ctk.CTkLabel(
            strategic_frame,
            text="Modo de Reprodução Estratégica",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#DAA520"
        )
        strategic_label.pack(pady=(10, 5))

        # Campo para inserir a condição
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
        # --------------------------------------------------------

        # --- Frame para Opções de Repetição ---
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

        # Radio button para reproduzir uma vez
        once_radio = ctk.CTkRadioButton(
            repeat_options_frame,
            text="Reproduzir uma vez",
            variable=self.repeat_mode,
            value="once",
            text_color="#F0F0F0",
            fg_color="#DAA520"
        )
        once_radio.pack(side="left", padx=10)

        # Radio button para reproduzir indefinidamente
        continuous_radio = ctk.CTkRadioButton(
            repeat_options_frame,
            text="Reproduzir indefinidamente",
            variable=self.repeat_mode,
            value="continuous",
            text_color="#F0F0F0",
            fg_color="#DAA520"
        )
        continuous_radio.pack(side="left", padx=10)

        # Campo para reproduzir N vezes
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
        # --------------------------------------------------------
        
        # Frame de status
        status_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        status_frame.pack(fill="both", expand=True)
        
        status_label = ctk.CTkLabel(
            status_frame,
            text="Status do Sistema",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#DAA520"
        )
        status_label.pack(pady=(10, 5))
        
        # Área de texto para status
        self.status_text = ctk.CTkTextbox(
            status_frame,
            width=700,
            height=120, # Reduzir altura para acomodar novos frames
            font=ctk.CTkFont(size=12),
            fg_color="#1A1A1A",
            text_color="#F0F0F0"
        )
        self.status_text.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Mensagem inicial
        self.update_status("Santzu iniciado. Pronto para a batalha da automação.")
        self.update_status("\"Conheça seu inimigo e conheça a si mesmo\" - Sun Tzu")
        
        # Frame de citações Sun Tzu
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
        # Hotkey para iniciar/parar gravação (F9)
        def on_f9():
            self.root.after(0, self.toggle_recording) # Executa na thread principal da GUI

        # Hotkey para iniciar/parar reprodução (F10)
        def on_f10():
            self.root.after(0, self.play_macro) # Executa na thread principal da GUI

        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<f9>': on_f9,
            '<f10>': on_f10
        })
        self.hotkey_listener.start()
        self.update_status("Hotkeys F9 (Gravar/Parar) e F10 (Reproduzir) ativadas.")

    def update_status(self, message):
        """Atualiza o status na interface"""
        self.status_text.insert("end", f"{message}\n")
        self.status_text.see("end")
        
    # --- NOVAS FUNÇÕES DE GERENCIAMENTO DE MACROS ---
    
    def refresh_macro_list(self):
        """Atualiza a lista de macros disponíveis"""
        self.macro_listbox.delete(0, tk.END)
        
        if os.path.exists(self.macros_dir):
            for filename in os.listdir(self.macros_dir):
                if filename.endswith('.json'):
                    # Remove a extensão .json para exibição
                    display_name = filename[:-5]
                    self.macro_listbox.insert(tk.END, display_name)
        
        self.update_status(f"Lista de macros atualizada. {self.macro_listbox.size()} macros encontradas.")
    
    def load_selected_macro(self):
        """Carrega a macro selecionada na lista"""
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
        """Salva uma nova macro com nome personalizado"""
        if not self.macro_recorder.events:
            messagebox.showwarning("Aviso", "Nenhuma macro para salvar.")
            return
        
        # Diálogo para inserir nome da macro
        dialog = ctk.CTkInputDialog(
            text="Digite o nome da nova macro:",
            title="Salvar Nova Macro"
        )
        macro_name = dialog.get_input()
        
        if macro_name:
            # Remove caracteres inválidos para nome de arquivo
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
        """Renomeia a macro selecionada"""
        selection = self.macro_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma macro da lista.")
            return
        
        old_name = self.macro_listbox.get(selection[0])
        old_filename = os.path.join(self.macros_dir, f"{old_name}.json")
        
        # Diálogo para inserir novo nome
        dialog = ctk.CTkInputDialog(
            text=f"Digite o novo nome para '{old_name}':",
            title="Renomear Macro"
        )
        new_name = dialog.get_input()
        
        if new_name:
            # Remove caracteres inválidos para nome de arquivo
            safe_name = "".join(c for c in new_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            new_filename = os.path.join(self.macros_dir, f"{safe_name}.json")
            
            try:
                os.rename(old_filename, new_filename)
                self.refresh_macro_list()
                self.update_status(f"✏️ Macro renomeada de '{old_name}' para '{safe_name}'.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao renomear macro: {str(e)}")
    
    def delete_selected_macro(self):
        """Exclui a macro selecionada"""
        selection = self.macro_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma macro da lista.")
            return
        
        selected_name = self.macro_listbox.get(selection[0])
        filename = os.path.join(self.macros_dir, f"{selected_name}.json")
        
        # Confirmação de exclusão
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
    
    # --- FIM DAS NOVAS FUNÇÕES DE GERENCIAMENTO ---
        
    def toggle_recording(self):
        """Alterna entre iniciar e parar a gravação"""
        if self.macro_recorder.playing:
            messagebox.showwarning("Aviso", "Não é possível iniciar a gravação enquanto uma macro está sendo reproduzida.")
            return

        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        """Inicia a gravação de macro"""
        self.is_recording = True
        self.record_button.configure(
            text="⏹️ PARAR GRAVAÇÃO (F9)",
            fg_color="#AA0000"
        )
        self.macro_recorder.start_recording()
        self.update_status("🔴 Gravação iniciada. Todas as ações estão sendo capturadas.")
        
    def stop_recording(self):
        """Para a gravação de macro"""
        self.is_recording = False
        self.record_button.configure(
            text="🔴 INICIAR GRAVAÇÃO (F9)",
            fg_color="#CC0000"
        )
        self.macro_recorder.stop_recording()
        self.update_status("⏹️ Gravação parada. Macro pronta para execução.")
        
    def play_macro(self):
        """Executa a macro gravada"""
        if self.macro_recorder.recording:
            messagebox.showwarning("Aviso", "Não é possível iniciar a reprodução enquanto uma macro está sendo gravada.")
            return

        if not self.macro_recorder.events:
            messagebox.showwarning("Aviso", "Nenhuma macro gravada ou carregada.")
            return
            
        self.update_status("▶️ Executando macro...")
        
        mode = self.repeat_mode.get()
        count = self.repeat_count.get() if mode == 'repeat_count' else 1

        # Executar em thread separada para não travar a interface
        threading.Thread(target=self._play_macro_thread, args=(mode, count), daemon=True).start()
        
    def _play_macro_thread(self, mode, count):
        """Thread para executar a macro"""
        try:
            # Passa o callback de avaliação de condições para o macro_recorder
            self.macro_recorder.play_macro(
                evaluate_conditions_callback=self.evaluate_condition,
                repeat_mode=mode,
                repeat_count=count
            )
            self.root.after(0, lambda: self.update_status("✅ Macro executada com sucesso."))
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"❌ Erro ao executar macro: {str(e)}"))

    def add_condition_to_next_event(self):
        """Adiciona uma condição ao próximo evento gravado"""
        condition_text = self.condition_entry.get()
        if not condition_text:
            messagebox.showwarning("Aviso", "Por favor, insira uma condição no campo de texto.")
            return

        if not self.macro_recorder.events:
            messagebox.showwarning("Aviso", "Nenhum evento gravado para adicionar condição.")
            return

        # Adiciona a condição ao último evento gravado
        self.macro_recorder.events[-1]["condition"] = condition_text
        self.update_status(f"Condição '{condition_text}' adicionada ao último evento gravado.")
        self.condition_entry.delete(0, ctk.END) # Limpa o campo de entrada

    def evaluate_condition(self, condition_str):
        """Avalia a string de condição e retorna True/False"""
        self.update_status(f"Avaliando condição: {condition_str}")
        # Exemplo de condições simples. Isso pode ser expandido para uma linguagem de script mais complexa.
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
                current_time_in_macro = time.time() - self.macro_recorder.start_time # Aproximado
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
            # Condição não reconhecida, assume como verdadeira
            self.update_status(f"Condição '{condition_str}' não reconhecida. Assumindo como verdadeira.")
            return True

    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()

if __name__ == "__main__":
    app = SantzuGUI()
    app.run()

