BINDIR = $(PWD)/.state/env/bin

# Short descriptions for commands (var format _SHORT_DESC_<cmd>)
_SHORT_DESC_DOCS := "Build docs"
_SHORT_DESC_PYENV := "Set up the python environment"
_SHORT_DESC_TESTS := "Run the tests"

default : help
	@echo "You must specify a command"
	@exit 1

# ###
#  Helpers
# ###

_REQUIREMENTS_FILES = requirements/main.txt requirements/docs.txt requirements/tests.txt
VENV_EXTRA_ARGS =

.state/env/pyvenv.cfg : $(_REQUIREMENTS_FILES)
	# Create our Python 3 virtual environment
	rm -rf .state/env
	python3 -m venv $(VENV_EXTRA_ARGS) .state/env

	# Upgrade tooling requirements
	$(BINDIR)/python -m pip install --upgrade pip setuptools wheel

	# Install requirements
	$(BINDIR)/python -m pip install $(foreach req,$(_REQUIREMENTS_FILES),-r $(req))

# /Helpers

# ###
#  Help
# ###

help :
	@echo ""
	@echo "Usage: make <cmd> [<VAR>=<val>, ...]"
	@echo ""
	@echo "Where <cmd> can be:"  # alphbetical please
	@echo "  * docs -- ${_SHORT_DESC_DOCS}"
	@echo "  * help -- this info"
	@echo "  * help-<cmd> -- for more info"
	@echo "  * pyenv -- ${_SHORT_DESC_PYENV}"
	@echo "  * tests -- ${_SHORT_DESC_TESTS}"
	@echo "  * version -- Print the version"
	@echo ""
	@echo "Where <VAR> can be:"  # alphbetical please
	@echo ""

# /Help

# ###
#  Pyenv
# ###

help-pyenv :
	@echo "${_SHORT_DESC_PYENV}"
	@echo "Usage: make pyenv"
	@echo ""
	@echo "Where <VAR> could be:"  # alphbetical please
	@echo "  * VENV_EXTRA_ARGS -- extra arguments to give venv (default: '$(VENV_EXTRA_ARGS)')"

pyenv : .state/env/pyvenv.cfg

# /Pyenv

# ###
#  Tests
# ###

TESTS =
TESTS_EXTRA_ARGS =

help-tests :
	@echo "${_SHORT_DESC_TESTS}"
	@echo "Usage: make tests [<VAR>=<val>, ...]"
	@echo ""
	@echo "Where <VAR> could be:"  # alphbetical please
	@echo "  * TESTS -- specify the test to run (default: '$(TESTS)')"
	@echo "  * TESTS_EXTRA_ARGS -- extra arguments to give pytest (default: '$(TESTS_EXTRA_ARGS)')"

tests : .state/env/pyvenv.cfg
	$(BINDIR)/pytest $(TESTS_EXTRA_ARGS) $(TESTS)

# /Tests

# ###
#  Version
# ###


curr_tag := $(shell git describe --tags $$(git rev-list --tags --max-count=1))
curr_tag_rev := $(shell git rev-parse "$(curr_tag)^0")
head_rev := $(shell git rev-parse HEAD)
head_short_rev := $(shell git rev-parse --short HEAD)
ifeq ($(curr_tag_rev),$(head_rev))
	version := $(curr_tag)
else
	version := $(curr_tag)-dev$(head_short_rev)
endif

version help-version : .git
	@echo $(version)

# /Version

# ###
#  Docs
# ###

help-docs :
	@echo "${_SHORT_DESC_DOCS}"
	@echo "Usage: make docs"

docs : .state/env/pyvenv.cfg
	$(MAKE) -C docs/ doctest SPHINXOPTS="-W" SPHINXBUILD="$(BINDIR)/sphinx-build"
	$(MAKE) -C docs/ html SPHINXOPTS="-W" SPHINXBUILD="$(BINDIR)/sphinx-build"

# /Docs
