PANDOC = pandoc
M4 = m4
PANFLG = --number-sections --pdf-engine=xelatex --standalone -M date="`date "+%B %e, %Y"`" --template=latex_template.tex
PDFS = cv.pdf resume.pdf accomplishments.pdf short_accomplishments.pdf

.PHONY: clean all $(PDFS)

all: $(PDFS)

$(PDFS):
	$(M4) $(subst .pdf,_template.md,$@) > $(subst .pdf,.md,$@)
	$(PANDOC) $(PANFLG) $(subst .pdf,.md,$@) -o $@

clean:
	rm -f *.pdf *.out *.log *.aux
