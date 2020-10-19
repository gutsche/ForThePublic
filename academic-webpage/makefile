M4=m4
DATE=$(shell date +"%d. %B %Y")

.PHONY: all clean server static

all:
	rm -f /tmp/_tmp1.md
	$(M4) templates/cv_template.md > /tmp/_tmp1.md
	cat /tmp/_tmp1.md | sed 's/AAAAAAAAAABBBBBBBBBBCCCCCCCCCC/$(DATE)/g' > content/cv/cv.md
	rm -f /tmp/_tmp1.md
	$(M4) templates/resume_template.md > /tmp/_tmp1.md
	cat /tmp/_tmp1.md | sed 's/AAAAAAAAAABBBBBBBBBBCCCCCCCCCC/$(DATE)/g' > content/resume/resume.md
	rm -f /tmp/_tmp1.md
	$(M4) templates/about_template.md > /tmp/_tmp1.md
	cat /tmp/_tmp1.md | sed 's/AAAAAAAAAABBBBBBBBBBCCCCCCCCCC/$(DATE)/g' > content/authors/gutsche/_index.md
	rm -f /tmp/_tmp1.md
	$(M4) templates/articles_template.md > /tmp/_tmp1.md
	cat /tmp/_tmp1.md | sed 's/AAAAAAAAAABBBBBBBBBBCCCCCCCCCC/$(DATE)/g' > content/articles/articles.md
	rm -f /tmp/_tmp1.md
	$(M4) templates/talks_template.md > /tmp/_tmp1.md
	cat /tmp/_tmp1.md | sed 's/AAAAAAAAAABBBBBBBBBBCCCCCCCCCC/$(DATE)/g' > content/talks/talks.md
	rm -f /tmp/_tmp1.md
	$(M4) templates/physics_pubs_template.md > /tmp/_tmp1.md
	cat /tmp/_tmp1.md | sed 's/AAAAAAAAAABBBBBBBBBBCCCCCCCCCC/$(DATE)/g' > content/physics_pubs/physics_pubs.md
	rm -f /tmp/_tmp1.md
	$(M4) templates/computing_pubs_template.md > /tmp/_tmp1.md
	cat /tmp/_tmp1.md | sed 's/AAAAAAAAAABBBBBBBBBBCCCCCCCCCC/$(DATE)/g' > content/computing_pubs/computing_pubs.md
	rm -f /tmp/_tmp1.md


clean:
	rm -f /tmp/_tmp1.md

server:
	hugo server -D --bind=0.0.0.0 --disableFastRender

static:
	hugo
