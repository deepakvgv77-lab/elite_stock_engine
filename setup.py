from setuptools import setup, find_packages

setup(
    name="elite_stock_engine",
    version="0.2.0",
    description="Elite Stock Recommendation Engine for Indian markets",
    author="Your Name or Organization",
    packages=find_packages(where="app"),
    package_dir={"": "app"},
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn[standard]>=0.23.1",
        "pydantic>=2.3.0",
        "duckdb>=0.8.1",
        "httpx>=0.25.0",
        "beautifulsoup4>=4.12.2",
        "loguru>=0.7.0",
        "tenacity>=8.2.2",
        "apscheduler>=3.10.0",
        "great_expectations>=0.18.4",
        "python-jose>=3.3.0",
        "icalendar>=4.0.9",
        "numpy>=1.26.1",
        "pandas>=2.1.0",
        "shap>=0.42.1",
        "joblib>=1.3.2",
        "openlineage-python>=0.26.1",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "elite-stock-engine=app.main:app",
        ],
    },
)
