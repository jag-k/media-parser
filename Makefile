generate_parser_schemas:
	@echo "Generating parser scheme..."
	@poetry run python -c "from media_parser.parsers import BaseParser; print(BaseParser.generate_schema())" > ./schemas/parser_schema.json
	@echo "Done!"

s_docs:
	@poetry run sphinx-build -b html docs/ dist/html

export_docs_deps:
	@poetry export -o docs/requirements.txt --with docs --without-hashes
