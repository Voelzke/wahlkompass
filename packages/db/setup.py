"""
Setup file for the wahlkompass-db package.
"""
from setuptools import setup

setup(
    name="wahlkompass-db",
    version="0.1.0",
    description="Database schema, migrations, and utilities for Wahlkompass",
    packages=[],
    py_modules=["init_season", "connection"],
    install_requires=[
        "psycopg2-binary>=2.9,<3",
    ],
    entry_points={
        "console_scripts": [
            "wahlkompass-init-season=init_season:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["schema.sql", "seed.sql", "seed_*.sql", "migrations/*.sql"],
    },
    python_requires=">=3.12",
)
