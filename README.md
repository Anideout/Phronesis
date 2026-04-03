# Phronesis - Discernimiento

NLP para textos. Soporta `.txt` y `.pdf`.

## Setup

```bash
# 1. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Descargar modelo de spaCy (español)
python -m spacy download es_core_news_sm
```

## Uso

```bash
# Análisis básico (txt o pdf)
python analizador.py analizar kierkegaard.txt
python analizador.py analizar hegel.pdf

# Top 20 palabras frecuentes
python analizador.py analizar texto.txt --top 20

# Análisis por capítulos
python analizador.py analizar texto.txt --capitulos

# Detectar entidades (personas, lugares)
python analizador.py analizar texto.txt --entidades

# Generar prosa pseudo-filosófica
python analizador.py analizar texto.txt --markov

# Todo junto + exportar reporte
python analizador.py analizar texto.pdf -c -e -m --exportar reporte.txt

# Ver estado de dependencias
python analizador.py info
```

## Flags

| Flag            | Corto | Descripción                        |
|-----------------|-------|------------------------------------|
| `--top N`       | `-n`  | N palabras más frecuentes (def 10) |
| `--capitulos`   | `-c`  | Sentimiento por capítulo/parte     |
| `--entidades`   | `-e`  | NER: personas, lugares, org        |
| `--markov`      | `-m`  | Generar prosa            |
| `--exportar`    | `-o`  | Guardar reporte en .txt            |

## En Neovim

```lua
-- Correr el script desde Neovim sin salir:
-- :!python analizador.py analizar %   (analiza el archivo actual)
-- :terminal                           (abre terminal integrada)
-- Usa Telescope para navegar entre corpus/ y el script
```

## Estructura

```
analizador/
├── analizador.py     ← script principal
├── requirements.txt
├── corpus/           ← pon tus .txt y .pdf aquí
└── output/           ← reportes exportados
```
