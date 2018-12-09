PANDOC = pandoc
M4 = m4
PANFLG = --pdf-engine=xelatex --standalone -M date="`date "+%B %e, %Y"`" --template=latex_template.tex
PDFS = test.pdf
HTMLS =

.PHONY: clean all $(PDFS) $(HTMLS)

all: $(PDFS) $(HTMLS)

$(PDFS):
	$(M4) $(subst .pdf,_template.md,$@) > $(subst .pdf,.md,$@)
	$(PANDOC) $(PANFLG) $(subst .pdf,.md,$@) -o $@

$(HTMLS):
	$(PANDOC) $(subst .html,.md,$@) -o $@

clean:
	rm -f *.html *.pdf *.out *.log *.aux
