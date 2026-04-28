from machine import Pin, I2C, PWM
import time
import ssd1306


# mapeamento do hardware

# display OLED via I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# saídas
led_status = Pin(2, Pin.OUT)  # indica que o tempo está correndo
led_alarme = Pin(15, Pin.OUT) # simula um alerta visual
buzzer = PWM(Pin(12), freq=1000, duty=0)


def atualizar_display(linha1, linha2="", linha3=""):
    # preenche tudo com a cor preta
    oled.fill(0)
    # escreve na parte de cima
    oled.text(linha1, 0, 15)
    # ecsreve na parte do meio
    oled.text(linha2, 0, 30)
    # escrve na parte de baixo
    oled.text(linha3, 0, 45)
    # manda o visor mostrar o conteúdo
    oled.show()

# pinos da placa onde linhas e colunas estão conectadas
PINOS_LINHAS = [13, 14, 27, 26]
PINOS_COLUNAS = [25, 33, 32, 18]

linhas = [Pin(p, Pin.OUT) for p in PINOS_LINHAS]
for l in linhas:
    l.value(1)

colunas = [Pin(p, Pin.IN, Pin.PULL_UP) for p in PINOS_COLUNAS]

MAPA_TECLAS = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

def ler_teclado():
    tecla = None
    for r in range(0, 4):
        linhas[r].value(0)
        for c in range(0, 4):
            if colunas[c].value() == 0:
                tecla = MAPA_TECLAS[r][c]
        linhas[r].value(1)
    
    return tecla

# constantes de estado (FSM)
ESTADO_CONFIG = 0
ESTADO_RODANDO = 1
ESTADO_ALARME = 2

# variáveis do sistema
estado_atual = ESTADO_CONFIG
tempo_restante = 0

# controles de tempo
# valores iniciais para controle de tempo e debounce
ultimo_tick_relogio = time.ticks_ms()

# controle de debounce do teclado
tecla_anterior = None
ultimo_tempo_tecla = time.ticks_ms()
tempo_debounce_tecla = 250

print("Sistema iniciado")

# trigger para o github actions 
print("Teste")

# mensagem introdutória
atualizar_display("Bem-vindoo,", "usuario!")
time.sleep(2)
atualizar_display("Digite o tempo:", f"{tempo_restante} s")

# loop principal
while True:
    # obter o tempo atual para controle de debounce e contagem
    tempo_atual = time.ticks_ms()

    tecla_atual = ler_teclado()
    tecla_valida = None

    if tecla_atual:
        if tecla_atual != tecla_anterior or time.ticks_diff(tempo_atual, ultimo_tempo_tecla) > tempo_debounce_tecla:
            tecla_valida = tecla_atual
            ultimo_tempo_tecla = tempo_atual
            print(f"Tecla pressionada: {tecla_valida}")

    tecla_anterior = tecla_atual

    # máquina de estados
    # estado 0: configuração do tempo
    if estado_atual == ESTADO_CONFIG:
        # led desligado, cronômetro desligado
        led_status.value(0) 
        # led desligado, alarme desligado
        led_alarme.value(0)
        # desliga o buzzer
        buzzer.duty(0) 

        atualizar_display("Digite o tempo:", f"{tempo_restante} s")

        if tecla_valida:
            if tecla_valida.isdigit():
                # desloca a casa decimal
                tempo_restante = (tempo_restante * 10) + int(tecla_valida)
                # limite de 9999 segundos
                if tempo_restante > 9999: 
                    tempo_restante = 9999
                atualizar_display("Digite o tempo:", f"{tempo_restante} s")
                
            elif tecla_valida == '*': # reseta o tempo selecionado
                tempo_restante = 0
                atualizar_display("Tempo Zerado")
                time.sleep(1)
                atualizar_display("Digite o tempo:", f"{tempo_restante} s")
                
            elif tecla_valida == '#' and tempo_restante > 0: # inicia o cronômetro
                estado_atual = ESTADO_RODANDO
                ultimo_tick_relogio = tempo_atual
                atualizar_display("Contando", "Tempo restante:", f"{tempo_restante} s")

    # estado 1: cronômetro rodando
    elif estado_atual == ESTADO_RODANDO:
        led_status.value(1) # led aceso, cronômetro rodando

        if time.ticks_diff(tempo_atual, ultimo_tick_relogio) >= 1000: # conta a passagem de 1 segundo
            tempo_restante -= 1 # diminui 1 segundo do tempo restante
            ultimo_tick_relogio = tempo_atual 
            atualizar_display("Contando", "Tempo restante:", f"{tempo_restante} s")
            print(f"Tempo restante: {tempo_restante} segundos")

            if tempo_restante <= 0:
                print("Atenção: Tempo esgotado!")
                print("Pressione * ou # para desligar o alarme.")
                estado_atual = ESTADO_ALARME # muda para estado de alarme

        # pausar o cronômetro
        if tecla_valida == '#':
            estado_atual = ESTADO_CONFIG
            atualizar_display("Cronometro", "pausado.")
            print(f"Cronômetro pausado, {tempo_restante} s restantes")
            time.sleep(1.5)

    # estado 2: alarme disparado
    elif estado_atual == ESTADO_ALARME:
        # led desligado, cronômetro parado
        led_status.value(0) 
        # led aceso, alarme ligado
        led_alarme.value(1) 
        # liga o buzzer
        buzzer.duty(512)
        atualizar_display("Alerta!", "Tempo esgotado", "Pres. * ou #")

        # condição para desligar o alarme
        if tecla_valida == '*' or tecla_valida == '#':
            buzzer.duty(0)
            tempo_restante = 0
            estado_atual = ESTADO_CONFIG
            atualizar_display("Alarme desligado")
            print("Alarme desligado")
            time.sleep(1)

    # pequena pausa para evitar uso excessivo da CPU
    time.sleep(0.1)

