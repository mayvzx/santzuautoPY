import json
import os

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return self._get_default_config()

    def _get_default_config(self):
        return {
            'hotkeys': {
                'record_toggle': '<f9>',
                'play_toggle': '<f10>',
                'pause_toggle': '<f11>' # Nova hotkey para pausar/retomar
            },
            'playback_speed': 'normal', # normal, slow, fast, custom
            'custom_playback_speed_multiplier': 1.0, # Multiplicador para velocidade customizada
            'macros_directory': 'macros',
            'log_level': 'INFO'
        }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_setting(self, key, default_value=None):
        keys = key.split(".")
        current_config = self.config
        for k in keys:
            if k in current_config:
                current_config = current_config[k]
            else:
                return default_value
        return current_config

    def set_setting(self, key, value):
        keys = key.split(".")
        current_config = self.config
        for i, k in enumerate(keys):
            if i == len(keys) - 1:
                current_config[k] = value
            else:
                if k not in current_config or not isinstance(current_config[k], dict):
                    current_config[k] = {}
                current_config = current_config[k]

if __name__ == '__main__':
    # Exemplo de uso
    config_manager = ConfigManager()
    print("Configurações iniciais:", config_manager.config)

    # Alterar uma hotkey
    config_manager.set_setting('hotkeys.record_toggle', '<f8>')
    print("Nova hotkey de gravação:", config_manager.get_setting('hotkeys.record_toggle'))

    # Alterar velocidade de reprodução
    config_manager.set_setting('playback_speed', 'fast')
    print("Nova velocidade de reprodução:", config_manager.get_setting('playback_speed'))

    # Adicionar uma nova configuração
    config_manager.set_setting('new_option.sub_option', True)
    print("Nova opção:", config_manager.get_setting('new_option.sub_option'))

    # Carregar novamente para verificar se as mudanças foram salvas
    new_config_manager = ConfigManager()
    print("Configurações após recarregar:", new_config_manager.config)

    # Limpar o arquivo de configuração para o próximo teste
    if os.path.exists('config.json'):
        os.remove('config.json')
        print("Arquivo config.json removido.")




