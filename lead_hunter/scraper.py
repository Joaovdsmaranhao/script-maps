
import re
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


class GoogleMapsScraper:

    def __init__(self):

        options = Options()
        options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(
            options=options
        )

    # ==========================================
    # PESQUISA
    # ==========================================

    def pesquisar(self, termo):

        self.driver.get(
            "https://www.google.com/maps"
        )

        time.sleep(3)

        # O Maps normalmente já deixa o campo focado
        campo = self.driver.switch_to.active_element

        campo.send_keys(termo)
        campo.send_keys(Keys.ENTER)

        print(f"\nPesquisando: {termo}")

        time.sleep(5)

    # ==========================================
    # COLETAR LINKS DOS ESTABELECIMENTOS
    # ==========================================

    def coletar_resultados(self):

        print("\nColetando estabelecimentos...")

        feed = self.driver.find_element(
            By.CSS_SELECTOR,
            'div[role="feed"]'
        )

        resultados = []
        urls_coletadas = set()

        tentativas_sem_novos = 0

        while True:

            cards = feed.find_elements(
                By.CSS_SELECTOR,
                'div[role="article"]'
            )

            novos = 0

            for card in cards:

                try:

                    texto = card.text.strip()

                    if not texto:
                        continue

                    linhas = [
                        linha.strip()
                        for linha in texto.split("\n")
                        if linha.strip()
                    ]

                    if not linhas:
                        continue

                    nome = linhas[0]

                    # Tenta encontrar o link do estabelecimento
                    links = card.find_elements(
                        By.TAG_NAME,
                        "a"
                    )

                    url = ""

                    for link in links:

                        href = link.get_attribute(
                            "href"
                        )

                        if href and "/maps/place/" in href:

                            url = href
                            break

                    # Sem URL não conseguimos abrir o estabelecimento
                    if not url:
                        continue

                    if url in urls_coletadas:
                        continue

                    urls_coletadas.add(url)

                    dados = self.extrair_dados(
                        linhas
                    )

                    dados["Nome"] = nome
                    dados["URL Google Maps"] = url

                    resultados.append(
                        dados
                    )

                    novos += 1

                except Exception as erro:

                    print(
                        f"Erro ao coletar card: {erro}"
                    )

            print(
                f"Links coletados: {len(resultados)} "
                f"| Novos: {novos}"
            )

            if novos == 0:

                tentativas_sem_novos += 1

            else:

                tentativas_sem_novos = 0

            if tentativas_sem_novos >= 3:

                print(
                    "\nFim dos resultados."
                )

                break

            # Rola a lista
            self.driver.execute_script(
                """
                arguments[0].scrollTop =
                    arguments[0].scrollHeight;
                """,
                feed
            )

            time.sleep(2)

        return resultados

    # ==========================================
    # EXTRAIR DADOS DO CARD
    # ==========================================

    def extrair_dados(self, linhas):

        nota = ""
        avaliacoes = ""
        preco = ""
        categoria = ""
        endereco = ""
        horario = ""

        for linha in linhas:

            # Nota + avaliações
            match = re.search(
                r'(\d[,.]\d)\s*\(([\d.]+)\)',
                linha
            )

            if match:

                nota = match.group(1)

                avaliacoes = (
                    match.group(2)
                    .replace(".", "")
                )

                # Preço
                preco_match = re.search(
                    r'(R\$\s*[\d.,]+\s*[–-]\s*R?\$?\s*[\d.,]+)',
                    linha
                )

                if preco_match:

                    preco = (
                        preco_match.group(1)
                    )

        # Categoria + endereço
        for linha in linhas:

            if " · " in linha:

                partes = [
                    parte.strip()
                    for parte in linha.split("·")
                    if parte.strip()
                ]

                if len(partes) >= 1:

                    categoria = partes[0]

                if len(partes) >= 2:

                    endereco = partes[-1]

                break

        # Horário
        for linha in linhas:

            if (
                "Aberto" in linha
                or "Fechado" in linha
            ):

                horario = linha
                break

        return {
            "Categoria": categoria,
            "Nota": nota,
            "Avaliações": avaliacoes,
            "Preço": preco,
            "Endereço": endereco,
            "Horário": horario
        }

    # ==========================================
    # COLETAR TELEFONE E SITE
    # ==========================================

    def coletar_detalhes(self, resultados):

        total = len(resultados)

        print(
            f"\nEncontrados {total} estabelecimentos."
        )

        print(
            "Iniciando coleta de telefone e site...\n"
        )

        for indice, resultado in enumerate(
            resultados,
            start=1
        ):

            nome = resultado["Nome"]
            url = resultado["URL Google Maps"]

            print(
                f"[{indice}/{total}] {nome}"
            )

            try:

                self.driver.get(url)

                time.sleep(2.5)

                telefone = self.buscar_telefone()

                site = self.buscar_site()

                resultado["Telefone"] = telefone
                resultado["Site"] = site

                print(
                    f"    Telefone: "
                    f"{telefone or 'Não encontrado'}"
                )

                print(
                    f"    Site: "
                    f"{site or 'Não encontrado'}"
                )

            except Exception as erro:

                print(
                    f"    Erro: {erro}"
                )

                resultado["Telefone"] = ""
                resultado["Site"] = ""

        return resultados

    # ==========================================
    # TELEFONE
    # ==========================================

    def buscar_telefone(self):

        try:

            elementos = self.driver.find_elements(
                By.CSS_SELECTOR,
                'button[data-item-id^="phone:"]'
            )

            if elementos:

                texto = elementos[0].text.strip()

                if texto:
                    return texto

        except Exception:
            pass

        # Segunda tentativa
        try:

            elementos = self.driver.find_elements(
                By.XPATH,
                '//button[contains(@aria-label, "Telefone")]'
            )

            for elemento in elementos:

                texto = elemento.text.strip()

                if texto:
                    return texto

        except Exception:
            pass

        return ""

    # ==========================================
    # SITE
    # ==========================================

    def buscar_site(self):

        try:

            elementos = self.driver.find_elements(
                By.CSS_SELECTOR,
                'a[data-item-id="authority"]'
            )

            if elementos:

                href = elementos[0].get_attribute(
                    "href"
                )

                if href:
                    return href

        except Exception:
            pass

        # Segunda tentativa
        try:

            elementos = self.driver.find_elements(
                By.XPATH,
                '//a[contains(@aria-label, "Website")]'
            )

            for elemento in elementos:

                href = elemento.get_attribute(
                    "href"
                )

                if href:
                    return href

        except Exception:
            pass

        return ""

    # ==========================================
    # QUALIFICAR LEAD
    # ==========================================

    def qualificar_lead(self, resultado):

        pontuacao = 0
        motivos = []

        site = resultado.get(
            "Site",
            ""
        )

        telefone = resultado.get(
            "Telefone",
            ""
        )

        nota = resultado.get(
            "Nota",
            ""
        )

        avaliacoes = resultado.get(
            "Avaliações",
            ""
        )

        # --------------------------
        # SEM SITE
        # --------------------------

        if not site:

            pontuacao += 5

            motivos.append(
                "Não possui site"
            )

        # --------------------------
        # TEM TELEFONE
        # --------------------------

        if telefone:

            pontuacao += 2

        # --------------------------
        # MUITAS AVALIAÇÕES
        # --------------------------

        try:

            quantidade = int(
                avaliacoes
            )

            if quantidade >= 500:

                pontuacao += 2

                motivos.append(
                    "Muitas avaliações"
                )

            elif quantidade >= 100:

                pontuacao += 1

        except:

            pass

        # --------------------------
        # NOTA ALTA
        # --------------------------

        try:

            nota_numero = float(
                nota.replace(",", ".")
            )

            if nota_numero >= 4.5:

                pontuacao += 1

                motivos.append(
                    "Nota alta"
                )

        except:

            pass

        # --------------------------
        # PRIORIDADE
        # --------------------------

        if pontuacao >= 7:

            prioridade = "🔥 ALTA"

        elif pontuacao >= 4:

            prioridade = "🟡 MÉDIA"

        else:

            prioridade = "⚪ BAIXA"

        resultado["Tem site?"] = (
            "SIM" if site else "NÃO"
        )

        resultado["Pontuação"] = pontuacao

        resultado["Prioridade"] = prioridade

        resultado["Motivo"] = (
            " + ".join(motivos)
            if motivos
            else "Poucos critérios encontrados"
        )

        return resultado

    # ==========================================
    # SALVAR EXCEL
    # ==========================================

    def salvar_excel(
        self,
        resultados,
        categoria,
        regiao
    ):

        print(
            "\nCalculando prioridades..."
        )

        for resultado in resultados:

            self.qualificar_lead(
                resultado
            )

        df = pd.DataFrame(
            resultados
        )

        # Remove duplicados
        df = df.drop_duplicates(
            subset=["Nome"]
        )

        # Região e busca
        df.insert(
            0,
            "Região",
            regiao
        )

        df.insert(
            1,
            "Busca",
            categoria
        )

        # Ordem das colunas
        colunas = [
            "Região",
            "Busca",
            "Nome",
            "Categoria",
            "Nota",
            "Avaliações",
            "Preço",
            "Endereço",
            "Telefone",
            "Site",
            "Tem site?",
            "Pontuação",
            "Prioridade",
            "Motivo",
            "Horário",
            "URL Google Maps"
        ]

        # Só utiliza colunas existentes
        colunas_existentes = [
            coluna
            for coluna in colunas
            if coluna in df.columns
        ]

        df = df[
            colunas_existentes
        ]

        # Ordena pelos melhores leads
        if "Pontuação" in df.columns:

            df = df.sort_values(
                by="Pontuação",
                ascending=False
            )

        nome_arquivo = (
            f"leads_{categoria}_{regiao}"
            .replace(" ", "_")
            .replace("/", "-")
        )

        nome_arquivo += ".xlsx"

        df.to_excel(
            nome_arquivo,
            index=False
        )

        print(
            "\n================================"
        )

        print(
            "      LEAD HUNTER FINALIZADO"
        )

        print(
            "================================"
        )

        print(
            f"Total de leads: {len(df)}"
        )

        if "Prioridade" in df.columns:

            print(
                "\nDistribuição:"
            )

            print(
                df["Prioridade"]
                .value_counts()
                .to_string()
            )

        print(
            f"\nArquivo: {nome_arquivo}"
        )

    # ==========================================
    # FECHAR
    # ==========================================

    def fechar(self):

        self.driver.quit()

