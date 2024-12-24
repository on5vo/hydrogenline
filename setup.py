from setuptools import setup, find_packages

setup(
    name="hydrogenline",
    version="0.1",
    packages=find_packages(),
    python_requires=">=3.10.7",
    install_requires=[
        "numpy",
        "matplotlib",
        "pyrtlsdr[lib]",
        "scipy",
        "tzlocal",
    ],
    entry_points={
        "console_scripts": [
            "capture=scripts.capture:main",
        ]
    }
)