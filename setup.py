from setuptools import setup, find_packages

setup(
    name="pr-reviewer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "react",
        "prismjs",
        "chart.js",
        "tailwindcss"
    ]
)
