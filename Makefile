# Simple Pandoc build for SpatialDDS spec
# Requires: pandoc (https://pandoc.org/) and a LaTeX engine for PDF (e.g., TeX Live / MacTeX)

SOURCES := $(shell ls spec/*.md | sort)
TITLE   := SpatialDDS: A Protocol for Real-World Spatial Computing
VERSION := 1.1
DATE    := September 2025
AUTHOR  := James Jackson

PDF  := SpatialDDS-$(VERSION).pdf
DOCX := SpatialDDS-$(VERSION).docx
HTML := SpatialDDS-$(VERSION).html

all: pdf

pdf:
\tpandoc $(SOURCES) \\\
\t  --metadata title="$(TITLE)" \\\
\t  --metadata author="$(AUTHOR)" \\\
\t  --metadata date="$(DATE)" \\\
\t  --standalone --toc \\\
\t  --pdf-engine=xelatex \\\
\t  -V geometry:margin=1in \\\
\t  -o $(PDF)

docx:
\tpandoc $(SOURCES) \\\
\t  --metadata title="$(TITLE)" \\\
\t  --metadata author="$(AUTHOR)" \\\
\t  --metadata date="$(DATE)" \\\
\t  --standalone --toc \\\
\t  -o $(DOCX)

html:
\tpandoc $(SOURCES) \\\
\t  --metadata title="$(TITLE)" \\\
\t  --metadata author="$(AUTHOR)" \\\
\t  --metadata date="$(DATE)" \\\
\t  --standalone --toc \\\
\t  -o $(HTML)

clean:
\trm -f $(PDF) $(DOCX) $(HTML)
