import os
import time
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright

def registrar_ponto():
    # Pega a hora EXATA de São Paulo/Brasília, ignorando o horário do servidor
    fuso_br = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_br)
    
    print(f"Robô acordou. Horário atual de Brasília: {agora.strftime('%H:%M:%S')}")

    # Define as janelas permitidas de acordo com o turno
    if agora.hour < 12:
        # Turno da Manhã
        inicio_janela = agora.replace(hour=7, minute=0, second=0, microsecond=0)
        fim_janela = agora.replace(hour=8, minute=10, second=0, microsecond=0)
    else:
        # Turno da Tarde
        inicio_janela = agora.replace(hour=17, minute=0, second=0, microsecond=0)
        fim_janela = agora.replace(hour=18, minute=0, second=0, microsecond=0)

    # =========================================================================
    # TRAVA DE SEGURANÇA 1: Passou do horário limite?
    # =========================================================================
    if agora > fim_janela:
        print("ERRO CRÍTICO: O GitHub iniciou a automação muito tarde devido a atrasos no servidor.")
        print("ABORTANDO EXECUÇÃO! O ponto NÃO será registrado para evitar marcação fora do horário.")
        return # Mata o script aqui, não faz mais nada.

    # =========================================================================
    # INTELIGÊNCIA DE TEMPO: Calculando a espera segura
    # =========================================================================
    segundos_para_esperar = 0
    
    if agora < inicio_janela:
        # O robô acordou cedo (ex: 06:45 ou 06:55). 
        # Ele calcula quanto falta até as 07:00, e depois sorteia um tempo extra seguro.
        segundos_ate_inicio = (inicio_janela - agora).total_seconds()
        tamanho_da_janela = (fim_janela - inicio_janela).total_seconds()
        
        # Sorteia um tempo dentro da janela, tirando 2 minutos (120s) de margem de segurança
        atraso_aleatorio = random.uniform(0, tamanho_da_janela - 120)
        segundos_para_esperar = segundos_ate_inicio + atraso_aleatorio
        
    else:
        # O robô acordou dentro da janela permitida (ex: 07:15).
        # Ele sabe que não pode esperar muito, então sorteia um atraso com base apenas no tempo que sobrou.
        segundos_restantes = (fim_janela - agora).total_seconds()
        # Sorteia um atraso garantindo que não vai passar do limite (tira 2 min de margem)
        atraso_aleatorio = random.uniform(0, max(0, segundos_restantes - 120))
        segundos_para_esperar = atraso_aleatorio

    minutos_espera = segundos_para_esperar / 60
    print(f"Calculo de segurança ativado. Aguardando {minutos_espera:.1f} minutos para iniciar a marcação...")
    time.sleep(segundos_para_esperar)

    hora_do_ponto = datetime.now(fuso_br)
    print(f"Atraso concluído! Iniciando o login agora às: {hora_do_ponto.strftime('%H:%M:%S')}")

    # =========================================================================
    # EXECUÇÃO DO PLAYWRIGHT
    # =========================================================================
    usuario = os.getenv("SITE_USUARIO")
    senha = os.getenv("SITE_SENHA")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # ALTERAÇÃO APLICADA: Configuração de tela Full HD e disfarce de navegador PC
        context = browser.new_context(
            geolocation={"latitude": -23.7245354, "longitude": -46.5618011},
            permissions=["geolocation"],
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto("https://intranet.csicargo.com.br/dp40")
            page.wait_for_load_state("networkidle")

            page.locator("input[type='text']").first.press_sequentially(usuario, delay=100)
            page.locator("input[type='password']").press_sequentially(senha, delay=100)
            
            page.wait_for_timeout(2000)
            page.locator("button:has-text('Acessar')").click()

            card_menu = page.locator("div.mud-card:has-text('Registro Ponto')")
            card_menu.wait_for(state="visible", timeout=20000)
            card_menu.click()

            botao_ponto = page.locator("button:has-text('Registrar Ponto')")
            botao_ponto.wait_for(state="visible", timeout=20000) 
            botao_ponto.click()
            
            page.wait_for_timeout(5000) 
            print("Ponto registrado com sucesso dentro da janela permitida!")

        except Exception as e:
            # ALTERAÇÃO APLICADA: Tirar foto do erro e forçar a falha no GitHub
            print(f"Erro ao tentar interagir com a página: {e}")
            page.screenshot(path="erro_tela.png")
            raise e # Garante que o GitHub fique vermelho para você ser avisado
            
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    registrar_ponto()
