from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pwmgr",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A secure local password manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pwmgr",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "cryptography>=41.0.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "pwmgr=pwmgr.cli:cli",
        ],
    },
) 