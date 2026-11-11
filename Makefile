.PHONY: bench lint sandbox-image

sandbox-image:
	docker build --tag reforge-sandbox:latest .

bench:
	python -m bench.run --manifest bench/corpus.yaml --config configs/experiments/hybrid.yaml

lint:
	ruff check src bench training tests
