
---

### 👤 Identificação do Candidato

- **Nome completo:** Rodrigo Pinheiro Alcantara
- **GitHub:** [rodrigop07](https://github.com/rodrigop07)

---

## 1️⃣ Visão Geral da Solução

O projeto consiste num **Temporizador de Intervalos e Descanso** implementado com ESP32. O objetivo é oferecer um sistema de cronometragem preciso para atividades que exigem tempos de pausa rigorosos, como treinos de hipertrofia ou processos industriais cíclicos. O sistema permite configurar o tempo usando um teclado numérico, iniciar/pausar a contagem e emite um alerta visual e sonoro quando o tempo se esgota, além de contar com um display I2C que torna a visualização da contagem do tempo e dos eventos muito agradáveis.

---

## 2️⃣ Arquitetura do Sistema Embarcado

A solução foi estruturada utilizando uma **Máquina de Estados Finita (FSM)** integrada num **Super Loop** assíncrono. 

- **Fluxo Principal:** O programa executa um ciclo contínuo que monitoriza entradas e atualiza saídas sem interromper o processamento da CPU com esperas passivas (`sleep`).
- **Estrutura de Estados:**
    - `ESTADO_CONFIG`: Estado inicial onde o usuário define o tempo desejado.
    - `ESTADO_RODANDO`: Estado ativo onde a contagem regressiva é decrescida segundo a segundo.
    - `ESTADO_ALARME`: Estado de alerta disparado ao atingir zero segundos.
- **Interação:** Os componentes interagem através de interrupções lógicas de software, garantindo que o sistema responda instantaneamente aos botões mesmo enquanto o cronômetro está rodando.

---

## 3️⃣ Componentes Utilizados na Simulação

Os componentes usados no arquivo `diagram.json` para simular o hardware real são:

- **Placa Microcontroladora:** ESP32-DevKit-C-V4.
- **Botão de Configuração (Pino 5):** Incrementa o temporizador de 5 em 5 segundos.
- **Botão de Controle (Pino 4):** Alterna entre Iniciar/Pausar e desliga o alarme.
- **LED de Status (Pino 2):** Indica visualmente que a contagem está em progresso.
- **LED de Alarme (Pino 15):** Sinaliza o término do intervalo programado.

---

## 4️⃣ Decisões Técnicas Relevantes

Para garantir um código eficiente e atender aos critérios de avaliação, foram usadas as seguintes estratégias:

- **Gestão de Tempo Não-Bloqueante:** Utilização da função `time.ticks_ms()` para calcular intervalos de tempo. Isto evita o uso de `time.sleep()`, permitindo que o sistema permaneça responsivo a comandos do utilizador a qualquer momento.
- **Debounce por Software:** Uso de uma janela de tempo (250ms) para validar as pressões dos botões, filtrando ruídos da simulação e garantindo acionamentos únicos.
- **Compatibilidade com CI/CD:** Inclusão de um comando de saída específico (`print("Teste")`) solicitado pelo pipeline de automação para validar a execução bem-sucedida do firmware nas GitHub Actions.
- **Alteração no DockerFile:** Para implementar o display OLED, o código do driver que o controla foi escrito em um arquivo diferente do `main.py`, o que fez necessária uma mudança no DockerFile que permitisse que todos os arquivos dentro da pasta `src` fossem lidos e executados no momento da execução da build.

---

## 5️⃣ Resultados Obtidos

O sistema mostrou plena estabilidade durante os testes de simulação:
- Os requisitos de lógica de firmware e organização de arquivos totalmente seguidos.
- A simulação no Wokwi executa a contagem regressiva com alta precisão.
- O projeto foi validado com sucesso pelo **GitHub Actions**, garantindo que a solução compila e executa corretamente no ambiente de correção automática.

---

## 6️⃣ Comentários Adicionais

A principal dificuldade encontrada foi a sincronização inicial entre o ambiente de build local e o pipeline do Wokwi CLI, que resolvida colocando um `print("Teste")` no código principal. Como melhoria futura, a implementação de uma placa wifi que permita conexões com outros dispositivos, alertando os eventos do cronômetro ou automatizando comandos em alguma tarefa específica.

---
