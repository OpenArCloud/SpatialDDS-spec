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
	pandoc $(SOURCES) \
	  --metadata title="$(TITLE)" \
	  --metadata author="$(AUTHOR)" \
	  --metadata date="$(DATE)" \
	  --standalone --toc \
	  --pdf-engine=xelatex \
	  -V geometry:margin=1in \
	  -o $(PDF)

docx:
	pandoc $(SOURCES) \
	  --metadata title="$(TITLE)" \
	  --metadata author="$(AUTHOR)" \
	  --metadata date="$(DATE)" \
	  --standalone --toc \
	  -o $(DOCX)

html:
	pandoc $(SOURCES) \
	  --metadata title="$(TITLE)" \
	  --metadata author="$(AUTHOR)" \
	  --metadata date="$(DATE)" \
	  --standalone --toc \
	  -o $(HTML)

clean:
	rm -f $(PDF) $(DOCX) $(HTML)
