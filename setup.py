from setuptools import setup, find_packages

setup(
    name="logicbridge",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.0.0",
        "sqlalchemy>=2.0.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
        "jsonschema>=4.0.0",
        "python-multipart>=0.0.6",
        "jinja2>=3.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        'console_scripts': [
            'logicbridge=logicbridge.cli:main',
        ],
    },
)