TARGETS = main
LATEXMK = latexmk

all:
	$(LATEXMK) -synctex=1 -xelatex  $(TARGETS)

clean:
	$(LATEXMK) -CA

.PHONY: all
