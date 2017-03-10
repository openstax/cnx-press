TEST_PATH = ./


# Short descriptions for commands (var format _SHORT_DESC_<cmd>)
_SHORT_DESC_TEST := "Run the tests"


default : help
	@echo "You must specify a command"
	@exit 1

help :
	@echo ""
	@echo "Usage: make <cmd> [<VAR>=<val>, ...]"
	@echo ""
	@echo "Where <cmd> can be:"  # alphbetical please
	@echo "  * help -- this info"
	@echo "  * help-<cmd> -- for more info"
	@echo "  * test -- ${_SHORT_DESC_TEST}"
	@echo ""
	@echo "Where <VAR> can be:"  # alphbetical please
	@echo ""

help-test :
	@echo "${_SHORT_DESC_TEST}"
	@echo "Usage: make test [<VAR>=<val>, ...]"
	@echo ""
	@echo "Where <VAR> could be:"
	@echo "  * TEST_PATH -- specify the test to run (default: './')"

test :
	pytest $(TEST_PATH)
