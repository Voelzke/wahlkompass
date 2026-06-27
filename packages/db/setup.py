"""
Setup file for the wahlkompass-db package.

Provides:
    - Database schema SQL (schema.sql, seed.sql)
    - init_season CLI tool
    - Connection utilities
"""
from setuptools import setup

setup(
    name="wahlkompass-db",
    version="0.1.0",
    description="Database schema, migrations, and utilities for Wahlkompass",
    package_dir={"": "."},
    packages=["db"],
    py_modules=["db"],
    install_requires=[
        "psycopg2-binary>=2.9",
    ],
    entry_points={
        "console_scripts": [
            "wahlkompass-init-season=db.init_season:main",
        ],
    },
    include_package_data=True,
    package_data={
        "db": ["schema.sql", "seed.sql", "migrations/*.sql"],
    },
    python_requires=">=3.12",
)
