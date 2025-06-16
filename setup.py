from setuptools import setup, find_packages
from pathlib import Path 

here = Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

VERSION = '1.0'
DESCRIPTION = 'RAG Document Viewer'

# Setting up
setup(
    name="rag-document-viewer",
    version=VERSION,
    author="Preprocess",
    author_email="<support@preprocess.co>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    license_files=('LICENSE',),
    install_requires=[
        "beautifulsoup4"
    ],
    python_requires='>=3.9',
    keywords=[
        'python', 'python3', 'preprocess', 'chunks', 'paragraphs', 'chunk',
        'paragraph', 'llama', 'llamaondex', "langchain", "chunking", "llm",
        "rag", "document", "view", "viewer", "preview", "previewer", "file"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)