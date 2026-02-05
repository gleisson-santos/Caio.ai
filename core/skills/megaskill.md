---
name: openclaw-mega-skill
description: Uma skill abrangente que encapsula toda a inteligência, arquitetura e funcionalidades do projeto OpenClaw. Use para entender o funcionamento do OpenClaw, replicar sua lógica em outros sistemas de IA ou implementar assistentes pessoais multicanal com capacidades avançadas de automação e voz.
---

# OpenClaw Mega Skill

Esta skill é um repositório completo de conhecimento sobre o ecossistema **OpenClaw**, um assistente de IA pessoal local-first. Ela fornece as diretrizes necessárias para que uma IA compreenda, opere e evolua a tecnologia por trás do OpenClaw, permitindo inclusive a criação de sistemas "irmãos" com capacidades similares.

## Capacidades Principais

O OpenClaw não é apenas um chatbot; é um **Gateway de Controle** para agentes de IA. Suas capacidades incluem:

1.  **Integração Multicanal:** Comunicação fluida via WhatsApp, Telegram, Slack, Discord, Signal, iMessage e outros, utilizando uma camada de abstração unificada.
2.  **Arquitetura Local-First:** Processamento centrado no dispositivo do usuário, garantindo privacidade e baixa latência.
3.  **Sistema de Habilidades (Skills):** Extensibilidade modular para interagir com ferramentas como Notion, Spotify, GitHub e automação residencial.
4.  **Interação por Voz:** Suporte a Wake Word (palavra de ativação) e Talk Mode (modo conversa) com síntese de voz de alta qualidade.
5.  **Espaço Visual (Canvas):** Interface dinâmica controlada pelo agente para exibição de dados e ferramentas interativas.

## Fluxo de Trabalho para IAs (ex: Gavity)

Para que outra IA possa utilizar este conhecimento para criar um "irmão" ou melhorar o sistema existente, siga estes passos:

### 1. Compreensão da Arquitetura
Consulte a seção "Arquitetura Técnica do OpenClaw" abaixo para entender como o Gateway gerencia as sessões e canais. O segredo da inteligência do OpenClaw reside na separação entre o **Plano de Controle** (Gateway) e o **Runtime do Agente** (Pi).

### 2. Replicação de Funcionalidades
Utilize a seção "Guia de Implementação de Funcionalidades OpenClaw" abaixo como guia para implementar:
-   **Normalização de Mensagens:** Como tratar diferentes protocolos de chat de forma idêntica.
-   **Gerenciamento de Ferramentas:** Como expor scripts e APIs para o LLM de forma segura.
-   **Automação:** Implementação de gatilhos baseados em tempo (Cron) ou eventos externos (Webhooks).

### 3. Estratégias de Melhoria
Para superar o OpenClaw original, foque em:
-   **RAG Avançado:** Implementar memória semântica persistente.
-   **Otimização de Custos:** Roteamento inteligente de prompts entre diferentes modelos de IA.
-   **Integração de Sistema:** Maior controle sobre o SO (macOS/Linux/Windows) através de comandos nativos e automação de interface.

## Recursos Disponíveis
-   Esta skill consolida todos os detalhes técnicos e de implementação.

## Quando usar esta Skill
-   Ao projetar um novo assistente de IA pessoal.
-   Para adicionar integrações de chat (WhatsApp/Telegram/etc.) a um sistema existente.
-   Ao buscar referências de como estruturar um sistema de agentes multimodais.
-   Para analisar e melhorar a segurança em interações de IA com canais públicos.

---

# Arquitetura Técnica do OpenClaw

## 1. Visão Geral
O **OpenClaw** é um assistente de IA pessoal projetado para rodar em hardware próprio (local-first). Ele atua como um **Gateway** (plano de controle) que gerencia sessões, canais de mensagens, ferramentas e eventos.

## 2. Componentes Principais
- **Gateway (Plano de Controle):** Gerencia conexões WebSocket, sessões, presença, cron jobs, webhooks e a interface de controle.
- **Canais (Channels):** Integrações com aplicativos de mensagens.
    - *Nativos:* WhatsApp (Baileys), Telegram (grammY), Slack (Bolt), Discord (discord.js), Signal (signal-cli), iMessage (AppleScript bridge).
    - *Extensões:* Microsoft Teams, Matrix, Zalo, BlueBubbles.
- **Runtime do Agente (Pi):** Motor de execução que suporta streaming de ferramentas e blocos.
- **Pipeline de Mídia:** Processamento de imagens, áudio (transcrição via Whisper) e vídeo.
- **Skills (Habilidades):** Sistema modular de extensões que permite ao assistente realizar tarefas específicas (ex: gerenciar notas no Notion, controlar Spotify, pesquisar GIFs).

## 3. Inteligência e Comportamento
- **Roteamento Multi-Agente:** Capacidade de rotear mensagens de diferentes canais para agentes isolados (workspaces).
- **Modo Talk e Voice Wake:** Suporte a voz sempre ativa com detecção de palavra de ativação (Wake Word) e síntese de voz (ElevenLabs).
- **Live Canvas:** Espaço de trabalho visual interativo (A2UI) que o agente pode manipular em tempo real.
- **Segurança (DM Policy):** Políticas rigorosas de emparelhamento para evitar processamento de mensagens de remetentes desconhecidos sem autorização explícita.

## 4. Tecnologias Utilizadas
- **Linguagem:** TypeScript (ESM).
- **Runtime:** Node.js 22+ ou Bun.
- **Comunicação:** WebSockets para o plano de controle.
- **Interface:** React/Vite para a UI de controle e Canvas.
- **Infraestrutura:** Docker para sandbox e deploy.

## 5. Como Replicar ou Criar um "Irmão"
Para criar um sistema similar (um "irmão" da IA), deve-se focar nos seguintes pilares:
1. **Abstração de Canais:** Criar uma interface unificada para que o agente trate mensagens de diferentes fontes da mesma forma.
2. **Plano de Controle Centralizado:** Um serviço que mantenha o estado das conexões e sessões de forma persistente.
3. **Sistema de Ferramentas (Tools):** Implementar um protocolo de chamada de funções (Function Calling) que permita ao LLM interagir com o sistema operacional e APIs externas.
4. **Interface Visual Dinâmica:** Prover uma forma do agente "mostrar" resultados complexos além de texto (como o Canvas do OpenClaw).
5. **Privacidade e Controle Local:** Priorizar o processamento local e o uso de chaves de API do próprio usuário.

---

# Guia de Implementação de Funcionalidades OpenClaw

## 1. Integração de Canais de Mensagens
A implementação de novos canais deve seguir o padrão de provedores do OpenClaw:
- **Handshake/Auth:** Cada canal requer um método de autenticação (QR Code para WhatsApp, Token para Telegram/Discord, OAuth para Slack).
- **Normalização de Mensagens:** Converter mensagens recebidas (texto, imagem, áudio) em um formato interno comum.
- **Gerenciamento de Estado:** Manter sessões ativas e lidar com reconexões automáticas.

## 2. Sistema de Skills (Habilidades)
As skills no OpenClaw são diretórios contendo:
- `SKILL.md`: Instruções para o modelo de linguagem.
- `scripts/`: Lógica executável.
- `references/`: Documentação adicional.
Para implementar uma nova funcionalidade, deve-se definir claramente o "contrato" entre o agente e a ferramenta.

## 3. Controle de Navegador (Browser Control)
O OpenClaw utiliza instâncias dedicadas de Chrome/Chromium para:
- Capturar snapshots de páginas.
- Realizar ações automatizadas (cliques, preenchimento de formulários).
- Extrair conteúdo para processamento pela IA.

## 4. Automação e Gatilhos (Triggers)
- **Cron:** Agendamento de tarefas recorrentes.
- **Webhooks:** Permite que serviços externos disparem ações no assistente.
- **Email Triggers:** Monitoramento de caixas de entrada para reagir a mensagens específicas.

## 5. Processamento de Voz e Mídia
- **Transcrição:** Uso de modelos como Whisper (local ou via API).
- **Síntese (TTS):** Integração com ElevenLabs para voz natural.
- **Visão Computacional:** Capacidade de analisar frames de vídeo e capturas de tela para entender o contexto visual do usuário.

## 6. Sugestões de Melhoria
Para evoluir o conceito do OpenClaw:
- **Memória de Longo Prazo:** Implementar uma base de dados vetorial (RAG) para que o assistente lembre de interações passadas de forma mais eficiente.
- **Orquestração de Múltiplos Modelos:** Alternar automaticamente entre modelos (ex: GPT-4 para tarefas complexas, Gemini para contextos longos) baseado no custo e necessidade.
- **Interface Mobile Nativa:** Expandir os "nodes" para aplicativos móveis mais robustos com integração profunda com o sistema operacional (atalhos, widgets).
