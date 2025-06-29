from PIL import Image
import mss
import numpy as np

def find_image_on_screen(template_path, confidence=0.9):
    """
    Procura uma imagem (template) na tela e retorna suas coordenadas se encontrada.
    Args:
        template_path (str): Caminho para o arquivo da imagem a ser procurada.
        confidence (float): Nível de confiança para a correspondência (0.0 a 1.0).
    Returns:
        tuple: (x, y, width, height) das coordenadas da imagem encontrada, ou None se não encontrada.
    """
    try:
        template = Image.open(template_path).convert("RGB")
        template_np = np.array(template)

        with mss.mss() as sct:
            # Captura a tela inteira
            monitor = sct.monitors[0]  # monitor principal
            sct_img = sct.grab(monitor)
            screen = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            screen_np = np.array(screen)

            # Implementação simplificada de busca (pode ser otimizada com OpenCV para performance)
            # Por enquanto, uma busca pixel a pixel para demonstração
            # Isso é EXTREMAMENTE ineficiente para imagens grandes ou telas inteiras
            # e serve apenas como um placeholder conceitual.
            # Uma implementação robusta usaria cv2.matchTemplate

            template_h, template_w, _ = template_np.shape
            screen_h, screen_w, _ = screen_np.shape

            for y in range(screen_h - template_h + 1):
                for x in range(screen_w - template_w + 1):
                    # Compara um pedaço da tela com o template
                    # Uma comparação mais sofisticada envolveria métricas de similaridade
                    # e tolerância a pequenas variações de pixel.
                    # Aqui, uma correspondência exata é esperada.
                    if np.array_equal(screen_np[y:y+template_h, x:x+template_w], template_np):
                        return (x, y, template_w, template_h)
        return None
    except Exception as e:
        print(f"Erro ao procurar imagem na tela: {e}")
        return None

# Exemplo de uso (para testes)
if __name__ == "__main__":
    # Crie um arquivo de imagem de teste (ex: 'test_template.png')
    # e coloque-o no mesmo diretório ou forneça o caminho completo.
    # Para um teste real, você precisaria de uma imagem pequena e única na tela.
    # Ex: um ícone de desktop, um botão de um programa, etc.
    
    # Exemplo de como criar um template simples para teste:
    # from PIL import Image, ImageDraw
    # img = Image.new('RGB', (50, 50), color = 'red')
    # d = ImageDraw.Draw(img)
    # d.text((10,10), "TEST", fill=(0,0,0))
    # img.save("test_template.png")

    print("Por favor, crie um arquivo 'test_template.png' para testar a detecção de imagem.")
    print("Coloque uma imagem pequena e única na sua tela para que o programa possa encontrá-la.")
    input("Pressione Enter para continuar quando a imagem estiver na tela...")

    found_coords = find_image_on_screen("test_template.png")
    if found_coords:
        print(f"Imagem encontrada em: {found_coords}")
    else:
        print("Imagem não encontrada na tela.")


