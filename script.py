"""
Autoclockin — registra ponto automaticamente dentro de uma janela segura.

Princípios de segurança (NÃO REMOVER):
1. NUNCA bater ponto fora da janela permitida.
2. NUNCA terminar com sucesso (exit 0) se o ponto não foi efetivamente
   confirmado pelo site. Qualquer dúvida → exit != 0 (workflow vermelho).
3. Verificação real de sucesso (não dormir e torcer).
4. Lockfile evita bater duas vezes no mesmo turno.
5. Screenshots e trace.zip salvos para diagnóstico.
"""

import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


FUSO_BR = ZoneInfo("America/Sao_Paulo")


def log(msg: str) -> None:
    agora = datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{agora}] {msg}", flush=True)


def fail(msg: str) -> None:
    """Imprime erro e termina com exit != 0 (workflow do GitHub fica vermelho)."""
    log(f"❌ ERRO CRÍTICO: {msg}")
    print(f"::error::{msg}", flush=True)  # marca o erro no log do GitHub Actions
    sys.exit(1)


def registrar_ponto() -> None:
    agora = datetime.now(FUSO_BR)
    log(f"Robô acordou. Horário atual de Brasília: {agora.strftime('%H:%M:%S')}")

    # =========================================================================
    # Define a janela permitida de acordo com o turno
    # =========================================================================
    if agora.hour < 12:
        turno = "manha"
        inicio_janela = agora.replace(hour=7, minute=0, second=0, microsecond=0)
        fim_janela = agora.replace(hour=8, minute=10, second=0, microsecond=0)
    else:
        turno = "tarde"
        inicio_janela = agora.replace(hour=17, minute=30, second=0, microsecond=0)
        fim_janela = agora.replace(hour=18, minute=30, second=0, microsecond=0)

    log(f"Turno detectado: {turno} | Janela: {inicio_janela.strftime('%H:%M')}–{fim_janela.strftime('%H:%M')}")

    # =========================================================================
    # LOCK: evita marcar duas vezes no mesmo turno (re-execuções manuais)
    # =========================================================================
    lock_file = Path(f".lock_{turno}_{agora.strftime('%Y%m%d')}")
    if lock_file.exists():
        fail(f"Já existe lock para o turno '{turno}' de hoje ({lock_file}). Ponto JÁ FOI registrado. Abortando.")

    # =========================================================================
    # TRAVA DE SEGURANÇA 1: Passou do horário limite?
    # =========================================================================
    if agora > fim_janela:
        fail(
            f"Acordei tarde demais ({agora.strftime('%H:%M:%S')}) — já passou de "
            f"{fim_janela.strftime('%H:%M')}. NÃO vou bater o ponto fora do horário."
        )

    # =========================================================================
    # INTELIGÊNCIA DE TEMPO: Calculando a espera segura
    # =========================================================================
    if agora < inicio_janela:
        segundos_ate_inicio = (inicio_janela - agora).total_seconds()
        tamanho_da_janela = (fim_janela - inicio_janela).total_seconds()
        atraso_aleatorio = random.uniform(0, max(0, tamanho_da_janela - 120))
        segundos_para_esperar = segundos_ate_inicio + atraso_aleatorio
    else:
        segundos_restantes = (fim_janela - agora).total_seconds()
        segundos_para_esperar = random.uniform(0, max(0, segundos_restantes - 120))

    minutos_espera = segundos_para_esperar / 60
    log(f"Aguardando {minutos_espera:.1f} minutos antes de marcar...")
    time.sleep(segundos_para_esperar)

    hora_do_ponto = datetime.now(FUSO_BR)
    log(f"Atraso concluído. Iniciando login às {hora_do_ponto.strftime('%H:%M:%S')}")

    # Revalidar janela DEPOIS do sleep (paranoia)
    if datetime.now(FUSO_BR) > fim_janela:
        fail("Após o sleep, já passou da janela permitida. PONTO NÃO REGISTRADO.")

    # =========================================================================
    # CREDENCIAIS
    # =========================================================================
    usuario = os.getenv("SITE_USUARIO")
    senha = os.getenv("SITE_SENHA")
    if not usuario or not senha:
        fail("Variáveis SITE_USUARIO/SITE_SENHA não definidas no ambiente.")

    # =========================================================================
    # EXECUÇÃO DO PLAYWRIGHT
    # =========================================================================
    sucesso = False
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            geolocation={"latitude": -23.7245354, "longitude": -46.5618011},
            permissions=["geolocation"],
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.set_default_timeout(30000)

        def snap(nome: str) -> None:
            try:
                page.screenshot(path=f"shot_{nome}.png", full_page=True)
            except Exception:
                pass

        try:
            log("Navegando para a página de login...")
            page.goto(
                "https://intranet.csicargo.com.br/dp40",
                wait_until="networkidle",
                timeout=60000,
            )
            snap("01_login_carregado")

            log("Preenchendo credenciais...")
            page.locator("input[type='text']").first.press_sequentially(usuario, delay=100)
            page.locator("input[type='password']").press_sequentially(senha, delay=100)
            page.wait_for_timeout(1500)
            snap("02_credenciais_preenchidas")

            log("Clicando em Acessar...")
            page.locator("button:has-text('Acessar')").click()
            page.wait_for_load_state("networkidle", timeout=30000)
            snap("03_pos_login")

            log("Procurando card 'Registro Ponto'...")
            card_menu = page.locator("div.mud-card:has-text('Registro Ponto')")
            card_menu.wait_for(state="visible", timeout=30000)
            card_menu.click()
            page.wait_for_load_state("networkidle", timeout=30000)
            snap("04_tela_registro_ponto")

            log("Procurando botão 'Registrar Ponto'...")
            botao_ponto = page.locator("button:has-text('Registrar Ponto')")
            botao_ponto.wait_for(state="visible", timeout=30000)

            # ÚLTIMA verificação de janela ANTES de clicar
            if datetime.now(FUSO_BR) > fim_janela:
                snap("05_abortado_fora_janela")
                fail("Passou da janela permitida momentos antes do clique. NÃO bati o ponto.")

            log("Clicando em Registrar Ponto AGORA...")
            botao_ponto.click()

            # =================================================================
            # VERIFICAÇÃO REAL DE SUCESSO (não confiar em sleep)
            # =================================================================
            log("Aguardando confirmação de sucesso na tela...")
            confirmado = False
            seletores_sucesso = [
                "div.mud-snackbar:has-text('sucesso')",
                "div.mud-alert-filled-success",
                "div:has-text('Ponto registrado')",
                "div:has-text('registrado com sucesso')",
                ".mud-snackbar",
            ]
            for sel in seletores_sucesso:
                try:
                    page.locator(sel).first.wait_for(state="visible", timeout=8000)
                    log(f"Confirmação encontrada via seletor: {sel}")
                    confirmado = True
                    break
                except PWTimeout:
                    continue

            page.wait_for_timeout(3000)
            snap("06_pos_clique")

            if not confirmado:
                fail(
                    "Cliquei em 'Registrar Ponto' mas NÃO encontrei mensagem de "
                    "confirmação. VERIFIQUE manualmente se o ponto foi registrado. "
                    "Veja shot_06_pos_clique.png nos artefatos."
                )

            log("✅ PONTO REGISTRADO COM SUCESSO E CONFIRMADO PELO SITE!")
            sucesso = True
            lock_file.write_text(datetime.now(FUSO_BR).isoformat(), encoding="utf-8")

        except PWTimeout as e:
            snap("99_erro_timeout")
            fail(f"Timeout ao interagir com a página: {e}")
        except SystemExit:
            raise
        except Exception as e:
            snap("99_erro_geral")
            fail(f"Erro inesperado ao tentar registrar o ponto: {e}")
        finally:
            try:
                context.tracing.stop(path="trace.zip")
            except Exception:
                pass
            context.close()
            browser.close()

    if not sucesso:
        fail("Saída do bloco Playwright sem confirmação de sucesso.")


if __name__ == "__main__":
    registrar_ponto()
