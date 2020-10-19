SUBDIRS = publication_list talk_list media_list cv profile academic-webpage

.PHONE: all

all:
	for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir all; \
	done
