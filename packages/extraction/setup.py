from setuptools import setup, find_packages

setup(
    name="wahlkompass-extraction",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary>=2.9,<3",
        "openai>=1.0,<2",
    ],
    python_requires=">=3.12",
)
