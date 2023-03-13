import cv2
import numpy as np
from tqdm import tqdm
import time
from termcolor import colored
import sys

# Escreve uma imagem compactada de 16 bits em um arquivo em formato proprietário
def write_16bits_image(new_img, filename, width, height):
    with open(filename, 'wb') as f:
        # Escreve largura e altura como cabeçalhos
        f.write(width.to_bytes(2, byteorder='little'))
        f.write(height.to_bytes(2, byteorder='little'))
        
        # Escreve pixels compactados
        for pixel in new_img:
            pixel_bin = pixel.to_bytes(2, byteorder='little')
            f.write(pixel_bin)

# Lê uma imagem compactada de 16 bits e retorna uma matriz numpy com os pixels
def read_16bits_image(filename):
    with open(filename, 'rb') as f:
        # Lê largura e altura a partir dos cabeçalhos
        width = int.from_bytes(f.read(2), byteorder='little')
        height = int.from_bytes(f.read(2), byteorder='little')
        
        # Lê pixels compactados
        pixels = f.read()
    return np.frombuffer(pixels, dtype=np.uint16).reshape((height, width))

# Descompacta os bits do canal de 16 bits para os canais R, G e B
def descompactar_bits(canal_16bits, bits_r, bits_g, bits_b):
    # Extrai os bits de cada canal
    mask_r = (1 << bits_r) - 1
    mask_g = (1 << bits_g) - 1
    mask_b = (1 << bits_b) - 1

    r_bits = (canal_16bits >> (bits_g + bits_b)) & mask_r
    g_bits = (canal_16bits >> bits_b) & mask_g
    b_bits = canal_16bits & mask_b
    
    # Reconstroi os canais R, G e B a partir dos bits extraídos
    r = int((r_bits << (8 - bits_r)) | (r_bits >> (2 * bits_r - 8)))
    g = int((g_bits << (8 - bits_g)) | (g_bits >> (2 * bits_g - 8)))
    b = int((b_bits << (8 - bits_b)) | (b_bits >> (2 * bits_b - 8)))
    
    return (r, g, b)

# Compacta os bits dos canais R, G e B em um único canal de 16 bits, de acordo com a escolha do usuário
def compactar_bits(r: int, g: int, b: int, bits_r: int, bits_g: int, bits_b: int) -> int:
    # Extrai os bits escolhidos pelo usuário
    mask_r = (1 << bits_r) - 1
    mask_g = (1 << bits_g) - 1
    mask_b = (1 << bits_b) - 1

    # Extrai os bits mais significativos de cada canal
    r_bits = (r >> (8 - bits_r)) & mask_r
    g_bits = (g >> (8 - bits_g)) & mask_g
    b_bits = (b >> (8 - bits_b)) & mask_b
    
    # Concatena os bits em um único número binário de 16 bits
    canal_16bits = (r_bits << (bits_g + bits_b)) | (g_bits << bits_b) | b_bits
    
    # Converte o número binário em um número inteiro de 16 bits
    return int(canal_16bits)

if len(sys.argv) != 4:
    print("\n{}\n{}\n". format(colored('Uso: python main.py <arquivo de entrada> <nome do arquivo de saída em formato proprietário> <arquivo de saída no formato desejado>', 'red', attrs=['bold']), colored('Exemplo: python main.py in.bmp out out.bmp', 'blue')))
    sys.exit(0)

# Nome do arquivo de entrada
in_file = sys.argv[1]

# Nome do arquivo compactado
out_dim_file = sys.argv[2]
out_dim_file += '.dim'

# Lê imagem original
img = cv2.imread(in_file)

# Lê a quantidade de bits para cada canal
while True:
    bits_r = int(input("Quantos bits para o canal R? "))
    bits_g = int(input("Quantos bits para o canal G? "))
    bits_b = int(input("Quantos bits para o canal B? "))

    if bits_r + bits_g + bits_b == 16:
        break
    else:
        print("\n{}\n". format(colored('Combinação inválida de bits! A soma dos bits deve ser igual a 16.', 'red', attrs=['bold'])))

# Cria uma lista para armazenar os pixels compactados
new_img = []

# Compacta os pixels da imagem original
print("\nCompactando pixels...\n")
for y in tqdm(range(0, img.shape[0])):
 for x in range(0, img.shape[1]):
    (b, g, r) = img[y, x]
    
    canal_16bits = compactar_bits(r, g, b, bits_r, bits_g, bits_b)

    new_img.append(canal_16bits)

# Escreve imagem compactada no formato proprietário
write_16bits_image(new_img, out_dim_file, img.shape[1], img.shape[0])

# Lê a imagem compactada
img_compactada = read_16bits_image(out_dim_file)

# Cria uma imagem vazia com as mesmas dimensões da imagem original
img_original = np.zeros((img_compactada.shape[0], img_compactada.shape[1], 3), dtype=np.uint8)

# Descompacta os pixels da imagem compactada
print("\nDescompactando pixels...\n")
for y in tqdm(range(0, img_compactada.shape[0])):
    for x in range(0, img_compactada.shape[1]):
        (r, g, b) = descompactar_bits(img_compactada[y, x], bits_r, bits_g, bits_b)
        img_original[y, x] = (b, g, r)

# Nome do arquivo descompactado
out = sys.argv[3]

print("\n{} {}!\n". format(colored('Imagem descompactada com sucesso e salva como', 'green', attrs=['bold']), out))

# Salva a imagem descompactada
cv2.imwrite(out, img_original)