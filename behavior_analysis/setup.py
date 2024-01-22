import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="behavior_analysis",
    version="0.0.1",
    author="Ulises Rey",
    author_email="ulises.rey@univie.ac.at",
    description="A small package to analyze worm behavior",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_namespace_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)