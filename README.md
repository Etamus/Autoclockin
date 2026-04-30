# Autoclockin

Este projeto consiste em uma automação desenvolvida em Python utilizando a biblioteca Playwright para interação com sistemas web baseados em Blazor (MudBlazor). O objetivo é realizar o login, navegação por menus e acionamento de botões de forma autônoma, simulando o comportamento humano e coordenadas geográficas específicas.

A execução é gerenciada pelo GitHub Actions, permitindo que o script rode de forma agendada em servidores na nuvem, eliminando a necessidade de um computador local ligado.

## Funcionalidades Principais

- **Agendamento Automático**: Execução programada para ocorrer duas vezes ao dia.  
- **Variabilidade de Horário**: Implementação de atraso aleatório (sleep) antes da execução para evitar registros em horários idênticos todos os dias.  
- **Simulação de Geolocalização**: Configuração de coordenadas de latitude e longitude no contexto do navegador para sistemas que exigem validação de GPS.  
- **Interação Humanizada**: Digitação sequencial com atraso entre caracteres e esperas baseadas em estados de rede, garantindo compatibilidade com o carregamento assíncrono do Blazor.  
- **Gestão de Credenciais**: Uso de GitHub Secrets para proteger dados sensíveis como usuário e senha.  

## Requisitos Técnicos

- Python 3.11 ou superior  
- Playwright (Framework de automação de navegador)  
- Python-dotenv (Para testes locais)  
- GitHub Actions (Ambiente de execução)  

## Estrutura do Projeto

- `script.py`: Código fonte principal contendo a lógica de navegação e registro.  
- `.github/workflows/main.yml`: Arquivo de configuração do pipeline de automação do GitHub.  
- `.env`: Arquivo (não versionado) utilizado para armazenar credenciais durante o desenvolvimento local.  

## Instruções para Configuração Local

Para validar o funcionamento do script em seu ambiente de desenvolvimento, siga os passos abaixo:

1. Instale as dependências necessárias:

    pip install playwright python-dotenv  
    playwright install chromium  

2. Crie um arquivo `.env` na raiz do projeto com o seguinte formato:

    SITE_USUARIO=seu_usuario  
    SITE_SENHA=sua_senha  

3. No arquivo `script.py`, certifique-se de que o parâmetro `headless` no lançamento do browser esteja definido como `False` para que você possa visualizar a execução:

    browser = p.chromium.launch(headless=False)

4. Execute o script:

    python script.py

## Configuração no GitHub Actions

Para que a automação funcione de forma independente na nuvem, as seguintes etapas são obrigatórias:

### 1. Variáveis de Ambiente (Secrets)

No menu **Settings > Secrets and variables > Actions** do seu repositório, adicione os seguintes segredos:

- `SITE_USUARIO`: O login de acesso ao sistema.  
- `SITE_SENHA`: A senha de acesso ao sistema.  

### 2. Permissões do Workflow

Em **Settings > Actions > General**, verifique se a opção **Workflow permissions** está definida como **Read and write permissions** para permitir que o GitHub execute as tarefas agendadas.

### 3. Agendamento (Cron)

O arquivo de workflow está configurado para disparar em dois momentos (Horário de Brasília):

- Entre **07:00 e 08:00** (gatilho inicial às 10:00 UTC)  
- Entre **17:30 e 18:30** (gatilho inicial às 20:00 UTC)  

O atraso aleatório é gerado internamente pelo script Python para garantir a variabilidade dentro desses intervalos.

## Segurança e Privacidade

Este repositório foi criado somente para fins educativos e de estudo. O uso de automações para registro de ponto pode estar sujeito a políticas internas da organização.
