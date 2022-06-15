from setuptools import find_packages, setup

setup(
    name="infrastructure",
    version=0.1,
    packages=find_packages(),
    package_data={},
    scripts=[],
    install_requires=[
        "aws-cdk-lib",
    ],
    extras_require={
        "test": ["pytest", "pylint!=2.5.0", "black", "mypy", "flake8", "pytest-cov"],
    },
    entry_points={
        "console_scripts": [],
    },
    classifiers=[],
    keywords="",
)
