import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mm-cli", # Replace with your own username
    version="0.0.3",
    author="Mass Mesh Technology Club",
    author_email="support@massmesh.org",
    description="A CLI application for connecting to the mesh. Written in Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MassMesh/mm-cli",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
	"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "argh",
        "netaddr"
    ],
)
