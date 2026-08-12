
from scraper import GoogleMapsScraper


def main():

    categoria = input(
        "O que você quer encontrar?: "
    ).strip()

    regiao = input(
        "Em qual cidade/região?: "
    ).strip()

    if not categoria or not regiao:

        print(
            "Categoria e região são obrigatórias."
        )

        return

    scraper = GoogleMapsScraper()

    try:

        termo = f"{categoria} em {regiao}"

        scraper.pesquisar(
            termo
        )

        resultados = scraper.coletar_resultados()

        resultados = scraper.coletar_detalhes(
            resultados
        )

        scraper.salvar_excel(
            resultados,
            categoria,
            regiao
        )

        input(
            "\nPressione ENTER para fechar..."
        )

    finally:

        scraper.fechar()


if __name__ == "__main__":
    main()

