# Variables
MKDOCS = mkdocs
CONFIG_FILE = /workspaces/ParagEkbote.github.io/mkdocs.yml

# Targets
.PHONY: serve build clean

serve:
	$(MKDOCS) serve -f $(CONFIG_FILE)

build:
	$(MKDOCS) build -f $(CONFIG_FILE)

clean:
	rm -rf site/
