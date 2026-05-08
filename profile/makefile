PANDOC = pandoc
HTMLS  = linkedin.html

.PHONY: all clean

all: $(HTMLS)

$(HTMLS):
	$(PANDOC) $(subst .html,.md,$@) -o $@

clean:
	rm -f *.html
