.PHONY: install clean run test

install:
	pip install -e .

clean:
	rm -rf build/ dist/ *.egg-info .nodeguard_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

run:
	nodeguard

test:
	# Add tests here when ready
	echo "No tests configured yet"
