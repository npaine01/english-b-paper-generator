# Build the IB English B Paper 2 templates.
#
#   make            build every PDF
#   make check      report question counts, mark totals and validation warnings
#   make proof      build the reading paper with answers printed in red
#   make clean      remove build products
#
# Tectonic hides package warnings from the console, so `make check` is how you
# see the mark-total and option-count checks before you print a paper.

TEX  := tectonic -X compile
DOCS := specimens new-paper paper1 reading-question-booklet \
        reading-text-booklet listening-booklet

all: $(addsuffix .pdf,$(DOCS)) markscheme.pdf

%.pdf: %.tex ibenglishb.sty
	$(TEX) $<

# the markscheme reads the .ans file the reading booklet writes
markscheme.pdf: markscheme.tex reading-question-booklet.pdf ibenglishb.sty
	$(TEX) markscheme.tex

check:
	@for f in $(DOCS); do \
	  printf '\n=== %s\n' "$$f"; \
	  $(TEX) --print $$f.tex 2>&1 \
	    | grep -E 'Package ibenglishb (Warning|Info)' -A1 \
	    | grep -vE '^--$$' | awk 'NF' | sort -u | sed 's/^/  /' > .chk; \
	  if [ -s .chk ]; then cat .chk; else echo '  OK'; fi; rm -f .chk; \
	done

# Regression check: compile adversarial content and machine-check that the
# measured layout rules still hold, in every shipped document as well.
breakdown:
	@for f in *.ans; do [ -f "$$f" ] && python3 tools/breakdown.py "$$f"; done

verify: all
	@cp ibenglishb.sty test/
	@cd test && $(TEX) torture.tex >/dev/null 2>&1
	@test -d test/.venv || (python3 -m venv test/.venv && \
	   test/.venv/bin/pip install --quiet pymupdf)
	@test/.venv/bin/python test/verify.py test/torture.pdf $(addsuffix .pdf,$(DOCS))

# The generator: a local editor with live PDF preview.
ui:
	@python3 ui/server.py

proof:
	$(TEX) --print reading-question-booklet.tex

clean:
	rm -f *.pdf *.ans *.log *.aux *.xdv
	rm -f test/*.pdf test/*.ans test/*.log test/*.aux test/*.xdv test/ibenglishb.sty
	rm -rf ui/build

.PHONY: all check clean proof verify ui breakdown
