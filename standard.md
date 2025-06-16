# Prerequisites Installation

Before installing **RAG Document Viewer**, you need to install several system dependencies that are required for the application to run properly and generate document views.

These packages and libraries are essential components that must be installed on your system to ensure **RAG Document Viewer** runs without issues and can generate views for your documents.

The following instructions are for Ubuntu systems. If you're using a different operating system, please find the equivalent commands for your distribution.

---

## 1. System Update

First, ensure your system is up to date and all packages are current:

```bash
sudo apt update
sudo apt upgrade
```

---

## 2. Install System Dependencies

Install the required system libraries that LibreOffice and pdf2htmlEX depend on:

```bash
sudo apt install libglib2.0-0 libfreetype6 libfontconfig1 libcairo2 libpng16-16 libjpeg-turbo8 libxml2 wget
```

---

## 3. LibreOffice Installation

LibreOffice is required for document processing. You can find installation instructions for your system [here](https://www.libreoffice.org/get-help/install-howto/).

For Ubuntu, install using:

```bash
sudo apt install libreoffice
```

Verify the installation by checking the version:

```bash
libreoffice --version
# Expected output example:
# LibreOffice 24.2.7.2 420(Build:2)
```

---

## 4. pdf2htmlEX Installation

Install pdf2htmlEX following the [official documentation](https://github.com/pdf2htmlEX/pdf2htmlEX/wiki/).

For Ubuntu, run the following commands:

```bash
wget https://github.com/pdf2htmlEX/pdf2htmlEX/releases/download/v0.18.8.rc1/pdf2htmlEX-0.18.8.rc1-master-20200630-Ubuntu-bionic-x86_64.deb -O /var/tmp/pdf2htmlEX.deb
sudo apt install -y /var/tmp/pdf2htmlEX.deb
```

Verify the installation:

```bash
pdf2htmlEX --version
# Expected output example:
# pdf2htmlEX version 0.18.8.rc1
# Libraries:
#   poppler 0.89.0
#   libfontforge (date) 20200314
#   cairo 1.18.0
# Supported image formats: png jpg svg
```

Clean up the downloaded package file:

```bash
rm -f /var/tmp/pdf2htmlEX.deb
```

---

## Installing RAG Document Viewer

Once all prerequisites are installed, you can install RAG Document Viewer using one of the following methods:

### Using pip:
```bash
pip install rag-document-viewer
```

### Using Poetry:
```bash
poetry add rag-document-viewer
poetry install
```

---

## Quick Start and Basic Usage

For quick start instructions and basic usage examples, please refer to the [main documentation](./README.md#quick-start).

---

## Troubleshooting

If you encounter any issues during installation:

1. Ensure all system dependencies are properly installed
2. Verify that LibreOffice and pdf2htmlEX are working correctly using the version commands above
3. Check that your system is up to date

---

## Roadmap

**Upcoming Features:**
- Stand alone docker image
- Support for additional operating systems

*Stay tuned for updates and new releases!*