from machine import Pin, I2C, PWM  # Controle de pinos, I2C e PWM (saída analógica)
import time                       # Funções de tempo (delays, ticks)
import network                    # Conectividade Wi-Fi
import urequests                  # Requisições HTTP para API do Telegram
import ujson                      # Conversão JSON para comunicação
import ssd1306                    # Driver do display OLED
import _thread                    # Execução de múltiplas threads


# credenciais da api do telegram
TOKEN_TELEGRAM = "8577374293:AAGU04F8Xb471uMJp2Zgelk7eT6kgM4SMDs"
CHAT_ID = None # inicialmente desconhecido, será aprendido na primeira mensagem recebida do usuário


# mapeamento do hardware
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

led_status = Pin(2, Pin.OUT)  
led_alarme = Pin(15, Pin.OUT) 
buzzer = PWM(Pin(12), freq=1000, duty=0)

def atualizar_display(linha1, linha2="", linha3=""):
    # função para atualizar o display OLED com até 3 linhas de texto
    oled.fill(0)                   # limpa o display (preenchimento com preto)
    oled.text(linha1, 0, 15)       # escreve primeira linha
    oled.text(linha2, 0, 30)       # escreve segunda linha
    oled.text(linha3, 0, 45)       # escreve terceira linha
    oled.show()                    # mostra o conteúdo no display

# funções de conectividade e IoT
def conectar_wifi():
    # conecta o microcontrolador à rede Wi-Fi para comunicação com a internet
    # tenta conectar até 10 vezes
    atualizar_display("Conectando...", "Rede Wi-Fi")
    wlan = network.WLAN(network.STA_IF)  # interface de station Wi-Fi
    wlan.active(True)                    # ativa o módulo Wi-Fi
    wlan.connect('Wokwi-GUEST', '')      # conecta à rede
    
    tentativas = 0
    while not wlan.isconnected() and tentativas < 10:
        time.sleep(1)
        tentativas += 1
        
    if wlan.isconnected():
        meu_ip = wlan.ifconfig()[0]
        print(f"Wi-Fi Conectado! IP: {meu_ip}")
        atualizar_display("Wi-Fi OK!", f"IP: {meu_ip}")
    else:
        print("Falha ao conectar no Wi-Fi")
        atualizar_display("Erro Wi-Fi", "Modo Offline")
        
    time.sleep(2) 

def enviar_notificacao_telegram(mensagem):
    # envia uma mensagem de notificação para o usuário via Telegram
    # só funciona se o token estiver configurado e o chat ID for conhecido
    # verifica se o token do bot foi configurado
    if TOKEN_TELEGRAM == "BOTFATHER_TOKEN":
        print("Aviso: Token não configurado")
        return

    # segurança: se não tiver ID, não tenta enviar
    # o ID é aprendido na primeira mensagem recebida do usuário
    if CHAT_ID is None:
        print("Aviso: O Bot ainda não sabe para quem enviar. Mande uma mensagem para ele no Telegram primeiro")
        return

    # constrói a URL da API do Telegram para enviar mensagem
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    headers = {'Content-Type': 'application/json'}
    
    # prepara os dados da mensagem em formato JSON
    payload = ujson.dumps({
        "chat_id": CHAT_ID,
        "text": mensagem
    })
    
    try:
        print("Enviando push para o Telegram")
        resposta = urequests.post(url, headers=headers, data=payload.encode('utf-8'))
        if resposta.status_code == 200:
            print("Notificação enviada com sucesso")
        resposta.close()
    except Exception as e:
        print(f"Erro ao enviar notificacao: {e}")

# polling multithreading
ultimo_update_id = 0

def checar_comandos_telegram():
    # consulta a API do Telegram para verificar novos comandos do usuário
    # executa em uma thread separada a cada 3 segundos
    # comandos suportados: /iniciar, /pausar, /zerar e números para ajustar tempo
    
    global ultimo_update_id, estado_atual, tempo_restante, ultimo_tick_relogio, CHAT_ID
    
    # sai da função se o token não estiver configurado
    if TOKEN_TELEGRAM == "COLE_O_TOKEN_DO_BOTFATHER_AQUI": return

    # URL para obter mensagens novas, offset garante que só recebe novas mensagens
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/getUpdates?offset={ultimo_update_id + 1}&timeout=0"
    
    try:
        resposta = urequests.get(url)
        dados = resposta.json()
        resposta.close()
        
        if dados.get("ok") and len(dados["result"]) > 0:
            for update in dados["result"]:
                ultimo_update_id = update["update_id"] 
                
                # verifica se a atualização contém uma mensagem de texto
                if "message" in update and "text" in update["message"]:
                    texto = update["message"]["text"].strip().lower()
                    
                    # vinculação do ID do usuário
                    # na primeira mensagem, o bot aprende com quem está conversando
                    novo_chat_id = update["message"]["chat"]["id"]
                    if CHAT_ID != novo_chat_id:
                        CHAT_ID = novo_chat_id
                        print(f"Novo chat vinculado, ID salvo: {CHAT_ID}")
                    
                    print(f"Comando recebido: {texto}")
                    
                    # comando: /iniciar - retoma o cronômetro se houver tempo configurado
                    if texto == "/iniciar" and tempo_restante > 0:
                        estado_atual = ESTADO_RODANDO
                        ultimo_tick_relogio = time.ticks_ms()
                        buzzer.duty(0)  # Desliga alarme
                        atualizar_display("Iniciado", "via Telegram!")
                        
                    # comando: /pausar - pausa o cronômetro
                    elif texto == "/pausar":
                        estado_atual = ESTADO_CONFIG
                        atualizar_display("Pausado", "via Telegram!")
                        
                    # comando: /zerar - limpa o tempo configurado e retorna ao modo de entrada
                    elif texto == "/zerar":
                        tempo_restante = 0
                        estado_atual = ESTADO_CONFIG
                        buzzer.duty(0)  # Desliga alarme
                        atualizar_display("Zerado", "via Telegram!")
                        
                    # comando: número - ajusta o tempo quando em modo de configuração
                    elif texto.isdigit() and estado_atual == ESTADO_CONFIG:
                        tempo_restante = int(texto)
                        if tempo_restante > 9999: tempo_restante = 9999
                        atualizar_display("Tempo Ajustado", f"{tempo_restante} s")
                        
    except Exception as e:
        pass 

def loop_background_telegram():
    # loop infinito que roda em uma thread separada.
    # consulta o Telegram a cada 3 segundos para novos comandos.
    # ignora erros para manter a thread rodando.

    while True:
        try:
            checar_comandos_telegram()
        except Exception:
            pass  # ignora erros de conexão ou timeout
        time.sleep(3)  # aguarda 3 segundos antes da próxima verificação 


# configuração do keypad 4x4
PINOS_LINHAS = [13, 14, 27, 26]      # pinos de controle das 4 linhas
PINOS_COLUNAS = [25, 33, 32, 18]     # pinos de leitura das 4 colunas

# inicializa os pinos de linhas como saída (OUTPUT)
linhas = [Pin(p, Pin.OUT) for p in PINOS_LINHAS]
for l in linhas:
    l.value(1)  # começa com valor 1 (não pressionado)

# inicializa os pinos de colunas com pull-up interno
# pull-up significa que o pino fica em nível alto quando não pressionado
colunas = [Pin(p, Pin.IN, Pin.PULL_UP) for p in PINOS_COLUNAS]

# mapa das teclas: posição corresponde ao layout do teclado 4x4
MAPA_TECLAS = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

def ler_teclado():
    # lê o teclado matricial 4x4 e retorna a tecla pressionada.
    # funciona por varredura: ativa uma linha por vez e verifica as colunas.
    # retorna None se nenhuma tecla está pressionada.
    
    tecla = None
    # varre cada linha do teclado
    for r in range(4):
        linhas[r].value(0)  # ativa a linha r 
        # verifica cada coluna para ver se há pressionamento
        for c in range(4):
            if colunas[c].value() == 0:  # coluna em nível baixo = tecla pressionada
                tecla = MAPA_TECLAS[r][c]  # obtém o caractere da tecla
        linhas[r].value(1)  # desativa a linha
    return tecla


# inicialização da FSM
# o sistema funciona com 3 estados distintos:
ESTADO_CONFIG = 0      # estado de configuração - usuário digita o tempo
ESTADO_RODANDO = 1     # estado de contagem - cronômetro em execução
ESTADO_ALARME = 2      # estado de alarme - tempo esgotado, alarme ativo

# variáveis de controle da máquina de estados
estado_atual = ESTADO_CONFIG         # estado inicial: aguardando entrada de tempo
tempo_restante = 0                  # tempo em segundos
notificacao_enviada = False         # flag para enviar notificação uma única vez

# variáveis para controle de tempo e entrada do teclado
ultimo_tick_relogio = time.ticks_ms()  # marca o tempo do último tick
tecla_anterior = None                  # armazena a tecla anterior (debouncing)
ultimo_tempo_tecla = time.ticks_ms()   # marca o tempo da última tecla pressionada
tempo_debounce_tecla = 250             # tempo em ms para evitar leituras duplicadas

print("Sistema iniciado")
conectar_wifi()

print("Iniciando núcleo secundário para IoT...")
_thread.start_new_thread(loop_background_telegram, ())

print("Teste") 
atualizar_display("Bem-vindo,", "Usuario!")
time.sleep(2)
atualizar_display("Digite o tempo:", f"{tempo_restante} s")


# loop principal da máquina de estados, roda indefinidamente no núcleo principal
# cada iteração verifica o estado, processa entradas e atualiza outputs

while True:
    tempo_atual = time.ticks_ms()  # obtém o tempo atual em milissegundos

    # leitura do keypad
    tecla_atual = ler_teclado()     # lê a tecla pressionada
    tecla_valida = None             # tecla que será processada (após debounce)

    # validação com debouncing para evitar leituras duplicadas
    if tecla_atual:
        # uma tecla é válida se é diferente da anterior OU se passou tempo suficiente
        if tecla_atual != tecla_anterior or time.ticks_diff(tempo_atual, ultimo_tempo_tecla) > tempo_debounce_tecla:
            tecla_valida = tecla_atual
            ultimo_tempo_tecla = tempo_atual
            print(f"Tecla pressionada: {tecla_valida}")

    tecla_anterior = tecla_atual  # armazena tecla atual para próxima iteração

    # estado 0: configuração do tempo
    if estado_atual == ESTADO_CONFIG:
        # desliga todos os indicadores visuais e sonoros
        led_status.value(0)         # LED verde desligado
        led_alarme.value(0)         # LED vermelho desligado
        buzzer.duty(0)              # buzzer silencioso
        notificacao_enviada = False # reseta flag para próximo alarme

        if tecla_valida:
            # construir o tempo de contagem
            if tecla_valida.isdigit():
                # multiplica por 10 e adiciona o novo dígito (ex: 5 vira 50, 50+3 = 53)
                tempo_restante = (tempo_restante * 10) + int(tecla_valida)
                # limita o tempo máximo a 9999 segundos 
                if tempo_restante > 9999: tempo_restante = 9999
                atualizar_display("Digite o tempo:", f"{tempo_restante} s")
                
            # tecla *: zerar o tempo (limpar entrada)
            elif tecla_valida == '*':
                tempo_restante = 0
                atualizar_display("Tempo Zerado")
                time.sleep(1)
                atualizar_display("Digite o tempo:", f"{tempo_restante} s")
                
            # tecla #: iniciar contagem (se houver tempo definido)
            elif tecla_valida == '#' and tempo_restante > 0:
                estado_atual = ESTADO_RODANDO
                ultimo_tick_relogio = tempo_atual
                atualizar_display("Contando", "Tempo restante:", f"{tempo_restante} s")

    # estado 1: cronômetro rodando
    elif estado_atual == ESTADO_RODANDO:
        led_status.value(1)  # LED verde aceso (indicador de funcionamento)

        # verifica se passou 1 segundo desde o último decremento
        if time.ticks_diff(tempo_atual, ultimo_tick_relogio) >= 1000:
            tempo_restante -= 1  # decrementa o tempo
            ultimo_tick_relogio += 1000  # avança o timestamp de referência
            atualizar_display("Contando", "Tempo restante:", f"{tempo_restante} s")
            print(f"Tempo restante: {tempo_restante} segundos")

            # ae o tempo chegou a zero, ativa o alarme
            if tempo_restante <= 0:
                print("Atenção: Tempo esgotado!")
                print("Pressione * ou # para desligar o alarme.")
                estado_atual = ESTADO_ALARME  # transição para estado de alarme

            # manda notificação no telegram a cada 30 segundos ou quando faltar 5 segundos para manter o usuário informado do progresso
            if tempo_restante % 30 == 0 or tempo_restante == 5:
                enviar_notificacao_telegram(f"Faltam {tempo_restante} segundos para o alarme tocar")

        # tecla #: pausa a contagem e volta ao modo de configuração
        if tecla_valida == '#':
            estado_atual = ESTADO_CONFIG
            atualizar_display("Cronometro", "pausado.")
            print(f"Cronômetro pausado, {tempo_restante} s restantes")
            time.sleep(1.5)

    # estado 2: alarme ativo (tempo esgotado)
    elif estado_atual == ESTADO_ALARME:
        led_status.value(0)  # LED verde desligado
        led_alarme.value(1)  # LED vermelho aceso (alarme ativo)
        buzzer.duty(512)     # buzzer em 50% da intensidade
        atualizar_display("Alerta!", "Tempo esgotado", "Pres. * ou #")

        # envia notificação via Telegram uma única vez
        if not notificacao_enviada:
            enviar_notificacao_telegram("ATENÇÃO: cronômetro chegou a zero! Fim do intervalo definido.")
            notificacao_enviada = True

        # tecla * ou #: Desliga o alarme e volta ao modo de configuração
        if tecla_valida == '*' or tecla_valida == '#':
            buzzer.duty(0)  # silencia o buzzer
            tempo_restante = 0  # limpa o tempo
            estado_atual = ESTADO_CONFIG  # retorna ao modo de configuração
            atualizar_display("Alarme desligado")
            print("Alarme desligado")
            time.sleep(1)

    # pausa de 10ms para evitar uso excessivo da CPU
    time.sleep(0.01)