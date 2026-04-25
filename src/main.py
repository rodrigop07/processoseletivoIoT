from machine import Pin
import time


# mapeamento do hardware
# entradas
btn_iniciar = Pin(4, Pin.IN, Pin.PULL_UP)
btn_tempo = Pin(5, Pin.IN, Pin.PULL_UP)

# saídas
led_status = Pin(2, Pin.OUT)  # indica que o tempo está correndo
led_alarme = Pin(15, Pin.OUT) # simula um alerta visual

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
ultimo_clique_iniciar = time.ticks_ms()
ultimo_clique_tempo = time.ticks_ms()
tempo_debounce = 250 # ms para evitar múltiplos cliques

print("Sistema iniciado")

# trigger para o github actions 
print("Teste")

# loop principal
while True:
    # obter o tempo atual para controle de debounce e contagem
    tempo_atual = time.ticks_ms()

    # leitura de dados de entrada
    clique_iniciar = False
    if btn_iniciar.value() == 0 and time.ticks_diff(tempo_atual, ultimo_clique_iniciar) > tempo_debounce:
        clique_iniciar = True
        ultimo_clique_iniciar = tempo_atual

    clique_tempo = False
    if btn_tempo.value() == 0 and time.ticks_diff(tempo_atual, ultimo_clique_tempo) > tempo_debounce:
        clique_tempo = True
        ultimo_clique_tempo = tempo_atual

    # máquina de estados
    # estado 0: configuração do tempo
    if estado_atual == ESTADO_CONFIG:
        led_status.value(0) # led desligado, cronômetro desligado
        led_alarme.value(0) # led desligado, alarme desligado

        if clique_tempo:
            tempo_restante += 5 # mais 5 segundos a cada clique
            print(f"Tempo configurado: {tempo_restante} segundos")

        if clique_iniciar and tempo_restante > 0:
            print("Cronômetro iniciado")
            estado_atual = ESTADO_RODANDO # mudar para estado de contagem
            ultimo_tick_relogio = tempo_atual # resetar o relógio para contagem

    # estado 1: cronÔmetro rodando
    elif estado_atual == ESTADO_RODANDO:
        led_status.value(1) # led aceso, cronômetro rodando

        if time.ticks_diff(tempo_atual, ultimo_tick_relogio) >= 1000: # conta a passagem de 1 segundo
            tempo_restante -= 1 # diminui 1 segundo do tempo restante
            ultimo_tick_relogio = tempo_atual 
            print(f"Tempo restante: {tempo_restante} segundos")

            if tempo_restante <= 0:
                print("Atenção: Tempo esgotado!")
                print("Pressione o botão 'Start/Pause' para desligar o alarme.")
                estado_atual = ESTADO_ALARME # muda para estado de alarme

        # pausa o cronômetro se o botão de iniciar for pressionado novamente
        if clique_iniciar:
            print("Cronômetro pausado")
            estado_atual = ESTADO_CONFIG # volta para estado de configuração

    # estado 2: alarme disparado
    elif estado_atual == ESTADO_ALARME:
        led_status.value(0) # led desligado, cronômetro parado
        led_alarme.value(1) # led aceso, alarme ligado

        # permanece nesse estado até algum botão ser pressionado
        if clique_iniciar or clique_tempo:
            print("Alarme desligado. Voltando para configuração.")
            tempo_restante = 0 # resetar o tempo
            estado_atual = ESTADO_CONFIG # volta para estado de configuração

    # pequena pausa para evitar uso excessivo da CPU
    time.sleep(0.1)


