import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="centerline",
    version="0.0.4",
    author="Ulises Rey",
    author_email="ulises.rey@imp.ac.at",
    description="A small package to extract centerlines from celegans worms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://bitbucket.vbc.ac.at/users/ulises.rey/repos/centerline/",
    packages=setuptools.find_namespace_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)