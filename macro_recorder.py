import json
import time
from pynput import mouse, keyboard
from vision_utils import find_image_on_screen # Importar a função de visão
from config_manager import ConfigManager # Importar ConfigManager
import threading

class MacroRecorder:
    def __init__(self, config_manager: ConfigManager):
        self.events = []
        self.recording = False
        self.playing = False
        self.paused = False # Nova variável de estado para pausa
        self.listener_mouse = None
        self.listener_keyboard = None
        self.start_time = None
        self.config_manager = config_manager # Referência ao gerenciador de configurações
        self._pause_event = threading.Event()
        self._pause_event.set() # Inicialmente não pausado

    def _on_press(self, key):
        if self.recording:
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key) # Para teclas especiais como Key.space, Key.enter

            self.events.append({
                'time': time.time() - self.start_time,
                'type': 'keyboard_press',
                'key': key_char,
                'condition': None
            })

    def _on_release(self, key):
        if self.recording:
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key)

            self.events.append({
                'time': time.time() - self.start_time,
                'type': 'keyboard_release',
                'key': key_char,
                'condition': None
            })

    def _on_click(self, x, y, button, pressed):
        if self.recording:
            self.events.append({
                'time': time.time() - self.start_time,
                'type': 'mouse_click',
                'x': x,
                'y': y,
                'button': str(button),
                'pressed': pressed,
                'condition': None
            })

    def _on_move(self, x, y):
        if self.recording:
            self.events.append({
                'time': time.time() - self.start_time,
                'type': 'mouse_move',
                'x': x,
                'y': y,
                'condition': None
            })

    def start_recording(self):
        if self.playing: # Trava: não pode gravar se estiver reproduzindo
            print("Não é possível iniciar a gravação enquanto uma macro está sendo reproduzida.")
            return
        if not self.recording:
            self.events = []
            self.recording = True
            self.start_time = time.time()
            self.listener_mouse = mouse.Listener(on_click=self._on_click, on_move=self._on_move)
            self.listener_keyboard = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self.listener_mouse.start()
            self.listener_keyboard.start()
            print("Gravação iniciada...")

    def stop_recording(self):
        if self.recording:
            self.recording = False
            if self.listener_mouse:
                self.listener_mouse.stop()
                self.listener_mouse.join()
            if self.listener_keyboard:
                self.listener_keyboard.stop()
                self.listener_keyboard.join()
            print("Gravação parada.")

    def save_macro(self, filename="macro.json"):
        with open(filename, 'w') as f:
            json.dump(self.events, f, indent=4)
        print(f"Macro salva em {filename}")

    def load_macro(self, filename="macro.json"):
        with open(filename, 'r') as f:
            self.events = json.load(f)
        print(f"Macro carregada de {filename}")

    def play_macro(self, evaluate_conditions_callback=None, repeat_mode='once', repeat_count=1):
        if self.recording: # Trava: não pode reproduzir se estiver gravando
            print("Não é possível iniciar a reprodução enquanto uma macro está sendo gravada.")
            return
        if self.playing: # Trava: não pode iniciar reprodução se já estiver reproduzindo
            print("Uma macro já está em reprodução.")
            return
        if not self.events:
            print("Nenhuma macro para reproduzir.")
            return

        self.playing = True # Define o estado de reprodução
        self.paused = False # Garante que não está pausado ao iniciar
        self._pause_event.set() # Garante que o evento de pausa está setado

        print("Reproduzindo macro...")
        mouse_controller = mouse.Controller()
        keyboard_controller = keyboard.Controller()

        # Obter configurações de velocidade
        playback_speed = self.config_manager.get_setting('playback_speed')
        custom_multiplier = self.config_manager.get_setting('custom_playback_speed_multiplier')

        speed_multiplier = 1.0
        if playback_speed == 'slow':
            speed_multiplier = 2.0
        elif playback_speed == 'fast':
            speed_multiplier = 0.5
        elif playback_speed == 'custom':
            speed_multiplier = custom_multiplier

        current_repeat = 0
        while self.playing and (repeat_mode == 'continuous' or current_repeat < repeat_count):
            start_play_time = time.time()
            for i, event in enumerate(self.events):
                self._pause_event.wait() # Espera se estiver pausado

                if not self.playing: # Permite parar a reprodução durante o loop
                    break

                if event['condition']:
                    if evaluate_conditions_callback:
                        condition_met = evaluate_conditions_callback(event['condition'])
                        if not condition_met:
                            print(f"Condição '{event['condition']}' não atendida. Pulando evento.")
                            continue # Pula o evento se a condição não for atendida
                    else:
                        print(f"Aviso: Condição '{event['condition']}' presente, mas sem callback de avaliação. Evento executado.")

                elapsed_time = time.time() - start_play_time
                time_to_wait = (event['time'] - elapsed_time) * speed_multiplier
                if time_to_wait > 0:
                    time.sleep(time_to_wait)

                if event['type'] == 'mouse_move':
                    mouse_controller.position = (event['x'], event['y'])
                elif event['type'] == 'mouse_click':
                    if event['pressed']:
                        mouse_controller.press(mouse.Button[event['button'].split('.')[-1]])
                    else:
                        mouse_controller.release(mouse.Button[event['button'].split('.')[-1]])
                elif event['type'] == 'keyboard_press':
                    key_str = event['key'].replace("'", "")
                    try:
                        # Tenta usar keyboard.Key para teclas especiais
                        keyboard_controller.press(getattr(keyboard.Key, key_str.split('.')[-1]))
                    except AttributeError:
                        # Para caracteres normais, usa o próprio caractere
                        keyboard_controller.press(key_str)

                elif event['type'] == 'keyboard_release':
                    key_str = event['key'].replace("'", "")
                    try:
                        # Tenta usar keyboard.Key para teclas especiais
                        keyboard_controller.release(getattr(keyboard.Key, key_str.split('.')[-1]))
                    except AttributeError:
                        # Para caracteres normais, usa o próprio caractere
                        keyboard_controller.release(key_str)
            
            if repeat_mode == 'once': # Sai do loop após a primeira execução se o modo for 'once'
                break
            current_repeat += 1
            print(f"Repetição {current_repeat} concluída.")

        self.playing = False # Reseta o estado de reprodução
        self.paused = False
        self._pause_event.set() # Garante que o evento de pausa está setado ao finalizar
        print("Reprodução da macro concluída.")

    def pause_playing(self):
        if self.playing and not self.paused:
            self.paused = True
            self._pause_event.clear() # Bloqueia a execução da macro
            print("Reprodução pausada.")

    def resume_playing(self):
        if self.playing and self.paused:
            self.paused = False
            self._pause_event.set() # Libera a execução da macro
            print("Reprodução retomada.")

    def stop_playing(self):
        """Para a reprodução da macro imediatamente"""
        self.playing = False
        self.paused = False
        self._pause_event.set() # Garante que qualquer espera seja liberada
        print("Reprodução da macro interrompida.")

if __name__ == '__main__':
    # Exemplo de uso (para testes, precisa de um config.json ou ConfigManager)
    # Este bloco provavelmente será removido quando integrado à GUI
    config_manager = ConfigManager()
    recorder = MacroRecorder(config_manager)
    print("Pressione 'r' para iniciar a gravação, 's' para parar, 'p' para reproduzir, 'l' para carregar, 'x' para salvar e 'q' para sair.")

    while True:
        try:
            user_input = input("> ")
            if user_input == 'r':
                recorder.start_recording()
            elif user_input == 's':
                recorder.stop_recording()
            elif user_input == 'p':
                recorder.play_macro()
            elif user_input == 'l':
                recorder.load_macro()
            elif user_input == 'x':
                recorder.save_macro()
            elif user_input == 'q':
                break
            elif user_input == 'pause':
                recorder.pause_playing()
            elif user_input == 'resume':
                recorder.resume_playing()
            elif user_input == 'stop':
                recorder.stop_playing()
        except Exception as e:
            print(f"Ocorreu um erro: {e}")






