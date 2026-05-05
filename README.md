
---

### 👤 Identificação do Candidato

- **Nome completo:** Rodrigo Pinheiro Alcantara
- **GitHub:** [rodrigop07](https://github.com/rodrigop07)

---

## 1️⃣ Visão Geral da Solução

O projeto consiste num **Temporizador de Intervalos e Descanso** implementado com ESP32. O objetivo é oferecer um sistema de cronometragem para atividades que exigem tempos de pausa rigorosos. A solução evoluiu para um dispositivo IoT bidirecional, permitindo a configuração do tempo fisicamente ou remotamente, além de fornecer acompanhamento visual em tempo real, alertas sonoros e notificações via [bot no Telegram](https://t.me/alarme_pnaat_esp32_bot). Para usá-lo, inicie o script e mande uma mensagem para o bot para sincronizá-lo com seu contato.

---

## 2️⃣ Arquitetura do Sistema Embarcado

A solução foi estruturada utilizando uma **Máquina de Estados Finita (FSM)** assíncrona, operando em conjunto com **Multithreading**.

- **Fluxo Principal (Núcleo Principal):** Um Super Loop não-bloqueante monitora o teclado, gerencia a passagem de tempo e atualiza os atuadores de hardware.
- **Fluxo Secundário (Núcleo Secundário):** Uma thread dedicada exclusivamente para consultar a API do Telegram a cada 3 segundos, impedindo que requisições web atrasem o cronômetro.
- **Estrutura de Estados:**
    - `ESTADO_CONFIG`: O usuário define o tempo desejado via teclado ou comandos via chat.
    - `ESTADO_RODANDO`: O cronômetro entra em contagem regressiva, com atualizações periódicas no display e notificações de progresso enviadas à nuvem.
    - `ESTADO_ALARME`: Alerta disparado ao atingir zero segundos, ativando LEDs, Buzzer e enviando a notificação final de conclusão.
- **Provisionamento Dinâmico:** O sistema inicia sem um ID fixo (`CHAT_ID = None`) e vincula-se automaticamente ao primeiro usuário que interagir com o bot.

---

## 3️⃣ Componentes Utilizados na Simulação

Os componentes e bibliotecas configurados para simular o hardware real são:

- **Placa Microcontroladora:** ESP32-DevKit-C-V4.
- **Teclado Numérico 4x4:** Para entrada de dados numéricos e navegação (Pinos de linha: 13, 14, 27, 26; Colunas: 25, 33, 32, 18). Use '*' para zerar o tempo e '#' para iniciar ou pausar a contagem.
- **Display OLED SSD1306 (I2C):** Interface gráfica principal para verificação de tempo e status de rede (Pinos 21 SDA, 22 SCL).
- **Buzzer (PWM):** Atuador sonoro operando a 1000Hz (Pino 12).
- **LED de Status (Pino 2):** Indica visualmente que a contagem está em progresso.
- **LED de Alarme (Pino 15):** Sinaliza o término do intervalo programado.
- **Conectividade Wi-Fi:** Uso da rede virtual `Wokwi-GUEST` e biblioteca `network` para tráfego de pacotes.

---


## 4️⃣ Como Usar o Bot do Telegram

O projeto possui integração bidirecional com o Telegram, permitindo o controle remoto total do temporizador de forma simples e intuitiva:

1. **Vinculação:** Como o sistema utiliza Provisionamento Dinâmico, basta iniciar a placa ESP32 e enviar qualquer mensagem (como um "Oi") para o bot no Telegram. O sistema capturará e salvará o seu ID de usuário automaticamente.
2. **Ajuste de Tempo:** Envie apenas números (ex: `45`) no chat para configurar os segundos do cronômetro quando ele estiver pausado ou zerado.
3. **Controle Remoto:** Utilize os comandos `/iniciar`, `/pausar` ou `/zerar` pelo chat para assumir o controle da máquina de estados de qualquer lugar do mundo.
4. **Notificações:** O bot enviará relatórios de progresso para o seu celular e um alerta final garantindo que você não perca o fim do seu tempo de descanso.
5. **Bot Próprio:** Foi disponibilizado um bot já pronto para uso, mas caso deseje, você pode criar seu bot pessoal do jeito que você quiser através do [BotFather](https://t.me/BotFather). Depois disso, é só colocar a chave da API do seu bot na variável global `TOKEN_TELEGRAM` no início do código e começar a usá-lo.

---

## 5️⃣ Decisões Técnicas Relevantes

Para garantir um código eficiente e atender aos critérios de sistemas embarcados conectados, foram adotadas as seguintes estratégias:

- **Gestão de Tempo Não-Bloqueante:** Utilização da função `time.ticks_ms()` para substituir o `time.sleep()` convencional, mantendo o controle reativo mesmo durante contagens.
- **Filtro de Ruído (Debounce):** Uso de uma janela temporal de 250ms por software para validar o acionamento mecânico dos botões do teclado.
- **Isolamento de Processos IoT:** Conexões HTTPS exigem poder de processamento para realizar a criptografia SSL/TLS. A biblioteca `_thread` transferiu esse peso lógico para um plano de fundo.
- **API REST Bidirecional:** Implementação nativa usando `urequests` e empacotamento `ujson` para formatar os payloads enviados ao webhook do Telegram em codificação UTF-8, além de realizar *polling* contínuo de comandos (`/iniciar`, `/pausar`, `/zerar`).
- **Alteração no DockerFile:** Para implementar o display OLED, o código do driver que o controla foi escrito em um arquivo diferente do `main.py`, o que fez necessária uma mudança no DockerFile que permitisse que todos os arquivos dentro da pasta `src` fossem lidos e executados no momento da execução da build.

---

## 6️⃣ Resultados Obtidos

O sistema alcançou o status de um produto de automação funcional e escalável:
- O hardware processa pacotes HTTP sem engasgos, mantendo a precisão temporal.
- O projeto soluciona de vez a limitação do terminal serial ao introduzir o display OLED como HUD primário.
- Validado de ponta a ponta com as automatizações de CI/CD solicitadas pelo desafio.
- O projeto foi validado com sucesso pelo **GitHub Actions**, garantindo que a solução compila e executa corretamente no ambiente de correção automática.

## 7️⃣ Comentários Adicionais

A principal dificuldade encontrada foi a sincronização inicial entre o ambiente de build local e o pipeline do Wokwi CLI, que resolvida colocando um `print("Teste")` no código principal. Como melhoria futura, a implementação de uma placa wifi que permita conexões com outros dispositivos, alertando os eventos do cronômetro ou automatizando comandos em alguma tarefa específica.

---
