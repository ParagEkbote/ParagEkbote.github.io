# Variables
MKDOCS = mkdocs

# Targets
.PHONY: serve build clean

serve:
	$(MKDOCS) serve

build:
	$(MKDOCS) build

clean:
	rm -rf site/
