def pytest_configure(config):
    config.addinivalue_line(
        "markers", "schemas: core object schema construction and validation"
    )
    config.addinivalue_line("markers", "instantiate: engine.instantiate() behaviour")
    config.addinivalue_line("markers", "rate: verifier.rate() and CA marking")
    config.addinivalue_line("markers", "failure_modes: named exception hierarchy")
