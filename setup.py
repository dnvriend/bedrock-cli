from setuptools import setup, find_packages

setup(
    name="bedrock-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "boto3",
        "psutil",
        "langchain_aws",
        "langchain_core",
        "langchain_community",
    ],
    entry_points={
        "console_scripts": [
            "bedrock=bedrock_cli.main:main",
        ],
    },
)