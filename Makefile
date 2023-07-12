generate_parser_schemas:
	@echo "Generating parser scheme..."
	@cd src && poetry run python -c "import parsers; print(parsers.BaseParser.generate_schema())" > ../schemas/parser_schema.json
	@echo "Done!"
