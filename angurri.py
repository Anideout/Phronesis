"""
Procesador de lenguaje natural para textos.
formato txt y pdf
"""

import typer
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
import time

# El motor que convertirá funciones en comandos de consola
app = type.Typer(
    name="Angurri",
    help="[bold purple] Phronesis[/]",
    # permite que las descripciones de ayuda tengan colores y estilos
    rich_markup_mode="rich",
)
# el objeto de Rich
console = Console()

"""
Carga de texto --------------------------------
"""


# basicamente leerá .txt dsp el path
def leer_txt(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8", errors="ignore")


# librería pdfplumber para los pdf
def leer_pdf(ruta: Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        console.print("[red]Instala pdfplumber:[/] pip install pdfplumber")
        raise typer.Exit(1)

    texto = []
    with pdfplumber.open(ruta) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto.append(t)
    return "\n".join(texto)


def cargar_texto(ruta: Path) -> str:
    sufijo = ruta.suffix.lower()
    if sufijo == ".pdf":
        console.print(f"[dim] Extrayendo texto del pdf... ({ruta.name})...[/]")
        return leer_pdf(ruta)
    elif sufijo == ".txt":
        return leer_txt(ruta)
    else:
        console.print(
            f"[red] Formato no soportado...{sufijo}(Solo se acepta .txt y .pdf"
        )
        raise typer.Exit(1)


"""
NLP helpers(El cerebro)
Funciones de apoyo para el Procesamiento de Lenguaje Natural.
"""


def cargar_spacy():
    try:
        import spacy

        try:
            return spacy.load("es_core_news_sm")
        except OSError:
            console.print(
                "[yellow] Modelo spacy no encontrado. Descargando es_core_news_sm...[/]"
            )
            import subprocess

            subprocess.run(
                [sys.executable, "-m", "spacy", "download", "es_core_news_sm"],
                check=True,
            )
            return spacy.load("es_core_news_sm")
    except ImportError:
        console.print("[red] Instala spacy: [/] pip install spacy")
        raise typer.Exit(1)


def frecuencias(doc, top_n: int = 15):
    from collections import Counter

    tokens = [
        t.lemma.lower()
        for t in doc
        if not t.is_stop and not t.is_punct and not t.is_space and len(t.text) > 2
    ]
    return Counter(tokens).most_common(top_n)


# TextBlob calcula la "polaridad"
def sentimiento_txtblob(texto: str):
    try:
        from textblob import TextBlob

        blob = TextBlob(texto)
        pol = blob.sentiment.polarity
        if pol > 0.1:
            return "positivo", pol
        elif pol < -0.1:
            return "negativo", pol

        return "neutro", pol
    except ImportError:
        return "neutro", 0.0


def analizar_sentimiento(texto: str):
    label, score = sentimiento_txtblob(texto)
    return label, round(score, 3)


# NER(Named Entity Recognition: Busca nombres de personas, lugares u organizaciones.)
def detectar_entidades(doc):
    from collections import Counter

    ents = [ent.text for ent in doc.ents if ent.label in ("PER", "LOC", "ORG", "MISC")]
    return Counter(ents).most_common(10)


# Regex(expresiones regulares: patrones que parezcan titulos de capitulos.)
def dividir_capitulos(texto: str):
    import re

    patron = re.compile(
        r"(?:cap[íi]tulo\s+[IVXLC\d]+|§\s*\d+|\bpart[e]?\s+[IVXLC\d]+)",
        re.IGNORECASE,
    )
    partes = patron.split(texto)
    cabeceras = patron.findall(texto)
    if len(partes) > 1:
        caps = {}
        for i, cab in enumerate(cabeceras):
            caps[cab] = partes[i + 1]
        return caps
    # Si no hay marcadores, dividir en tercios
    n = len(texto)
    return {
        "parte I": text[: n // 3],
        "parte II": texto[n // 3 : 2 * n // 3],
        "parte III": texto[2 * n // 3],
    }


# creación de bot probabilistico basado en el texto. Elaborará frases coherentes en lo posible
def generar_markov(texto: str, num_oraciones: int = 3):
    try:
        import markovify
    except ImportError:
        return "[dim] Instala markovify para activar el generador: pip install markovify[/]"

    try:
        modelo = markovify.Text(texto, state_size=2)
        oraciones = []
        for _ in range(num_oraciones * 5):
            s = modelo.make_sentence(tries=100)
            if s:
                oraciones.append(s)
            if len(oraciones) >= num_oraciones:
                break
        if not oraciones:
            return "[dim] No se pudo genrar prosa (corpus muy pequeño.[/]"
        return " ".join(oraciones[:num_oraciones])
    except Exception as e:
        return f"[dim]Error Markov: {0}[/]"


# Visualización---------------------------
# Diseño del CLI que funcionará desde terminal obvis


def barra(valor: float, maximo: float, ancho: int = 25, color: str = "purple") -> str:
    llenas = int((valor / maximo) * ancho) if maximo > 0 else 0
    return f"[{color}]{'█' * llenas}[/{color}][dim]{'░' * (ancho - llenas)}[/dim]"


def color_sentimiento(label: str) -> str:
    return {"positivo": "green", "negativo": "red", "neutro": "yellow"}.get(
        label, "white"
    )


# Comandos---------------------------
@app.command()
def analizar(
    archivo: Path = typer.Argument(..., help="Ruta al .txt o .pdf a analizar"),
    top: int = type.Option(10, "-top", "-n", help="N palabras más frecuentes"),
    capitulos: bool = typer.Option(
        False, "--capitulos", "-C", help="Analizar por capitulos/partes"
    ),
    markov: bool = Typer.Option(False, "--markov", "-m", help="Generar prosa"),
    entidades: bool = typer.Option(
        False, "--entidades", "-e", help="Mostrar entidades detectadas"
    ),
    exportar: Optional[Path] = typer.Option(
        None, "--exportar", "-o", help="Guardar reporte en .txt"
    ),
):

    if not archivo.exists():
        console.print(f"[red]Archivo no encontrado:[/] {archivo}")
        raise typer.Exit(1)
    console.print()
    console.print(
        Panel.fit(
            "[bold pruple] Phronesis",
            border_style="purple",
        )
    )
    console.print()

    with Progress(
        SpinnerColumn(), TextColumn("{task.description"), console=console
    ) as prog:
        t1 = prog.add_task("Cargando texto...", total=None)
        texto = cargar_texto(archivo)
        prog.update(t1, description="[green] Texto cargado![/]", complete=True)
        time.sleep(0.2)

        t2 = prog.add_task("procesando con spacy...", total=None)
        nlp = cargar_spacy()
        # procesar en chunks si el texto es muy largo
        max_chars = 1_000_000
        doc = nlp(texto[:max_chars])
        prog.update(t2, description="[green] Procesamiento NLP listo[/]", complete=True)
        time.sleep(0.2)

    palabras = texto.split()
    oraciones = list(doc.sents)
    vocab = set(t.lemma_.lower() for t in doc if t.is_alpha)
    ttr = round(len(vocab) / len(palabras) * 100, 1) if palabras else 0
    long_media = round(len(palabras) / len(oraciones), 1) if oraciones else 0

    # --Estadisticas generales
    console.rule("[bold purple]Estadisticas generales[/]")
    tabla = Table(box=box.SIMPLE, show_headeR=False, padding=(0, 2))
    tabla.add_column(style="dim")
    tabla.add_column(style="bold")
    tabla.add_row("Palabras totales", f"{len(palabras):,}")
    tabla.add_row("Vocabulario único", f"{len(vocab):,}")
    tabla.add_row("TTR (riqueza lexica)", f"{ttr}")
    tabla.add_row("Oraciones", f"{len(oraciones):,}")
    tabla.add_row("Long. media oración", f"{long_media} palabras")
    tabla.add_row("Caracteres", f"{len(texto):,}")
    console.print(tabla)

    # -- Frecuencias
    console.rule("[bold purple] Palabras más frecuentes[/]")
    freqs = frecuencias(doc, top_n=top)
    if freqs:
        maximo = freqs[0][1]
        for palabra, cnt in freqs:
            bar = barra(cnt, maximo, ancho=20)
    console.print(f" [cyan]{palabra:<20}[/] {bar} [dim] {cnt}[/]")
    console.print()

    # ----Sentimiento general
    console.rule("[bold purple] Sentimiento del texto[/]")
    label, score = analizar_sentimiento(texto[:50_000])
    color = color_sentimiento(label)
    console.print(f"Tono general: [{color}]{label}[/] [dim](score: {score})[/]")
    console.print()

    # --- Por capitulos
    if capitulos:
        console.rule("[bold purple] Analisis por capitulos[/]")
        caps = dividir_capitulos(texto)
        for nombre, fragmento in caps.items():
            if not fragmento.strip():
                continue
            lbl, sc = analizar_sentimiento(fragmento[:10_000])
            color = color_sentimiento(lbl)
            bar = barra(abs(sc), 1.0, ancho=15, color=color)
            console.print(
                f" [bold]{nombre: <14}[/] [{color}]{lbl:<10}[/] {bar} [dim]{sc:+.3f}[/]"
            )
        console.print()

    # --- Entidades
    if entidades:
        console.rule("[bold purple] entidades detectadas (NER) [/]")
        ents = detectar__entidades(doc)
        if ents:
            for ent, cnt in ents:
                console.print(f"[magenta]{ent:<25}[/] [dim]x{cnt}[/]")

        else:
            console.print(" [dim] No se detectaron entidades significativas.[/]")
        console.print()

    # --- Markov
    if markov:
        console.rule("[bold purple] Prosa pseudo-filosófica (Markov)[/]")
        prosa = generar_markov(texto)
        console.prnt(
            Panel(
                f"[italic]{prosa}[/italic]",
                border_style="dim purple",
                padding=(1, 2),
            )
        )
        console.print()

    if exportar:
        reporte = [
            "Phronesis - Reporte",
            "=" * 40,
            f"Archivo: {archivo}",
            f"Palabras: {len(palabras):,}",
            f"Vocabulario único: {len(vocab):,}",
            f"TTR: {ttr}%",
            f"Sentimiento: {label} ({score})",
            "",
            "Palabras más frecuentes",
        ]
        for p, c in freqs:
            reporte.append(f"{p}, {c}")
        exportar.write_text("\n".join(reporte), encoding="utf-8")
        console.print(f"[gree] Reporte guardado en[/] {exportar}")


@app.command()
def info():
    # Muestra dependencias y estado del entorno.
    deps = {
        "spacy": "NLP Principal",
        "pdfplumber": "Lectura de PDF's",
        "textblob": "Analisis de Sentimiento",
        "markovify": "generador de prosa",
        "rich": "Interfaz en terminal",
        "typer": "CLI",
    }
    console.print()
    console.rule("[purple] Estado el entorno[/]")
    for lib, desc in deps.items():
        try:
            __import__(lib)
            estado = "[gree] Instalado[/]"
        except ImportError:
            estado = "[red] falta[/]"
        console.print(f"{lib:<15} {estado} [dim]{desc}[/]")
    console.print()


if __name__ == "__main__":
    app()
