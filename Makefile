default : help
	@echo "You must specify a command"
	@exit 1

help :
	@echo ""
	@echo "Usage: make <cmd> [<VAR>=<val>, ...]"
	@echo ""
	@echo "Where <cmd> can be:"  # alphbetical please
	@echo "  * help -- this info"
	@echo ""
	@echo "Where <VAR> can be:"  # alphbetical please
	@echo ""
