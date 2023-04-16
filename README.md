# GCFPack - The CGF file packer

GCFPack is a low level GCF file packaging tool. It ingests a description file and one or more
data files and outputs a GCF archive.

The description file is formatted as JSON and provides all GCF and resource metadata. The
data files are the resources to be included in the GCF file. **GCFPack does not alter the given resources**,
nor will it check data validity. This means image resources must be stored raw.

GCFPack is mainly intended for use in data pipelines, with automated tools generating the description files
and converting the data accordingly.

## Usage

To run GCFPack, execute

```
python -mgcfpack
```

This will show the available commands.

## Development

To install the development tools, run:

```bash
# Create new environment
pipenv --python 3

# Install dependencies, including dev dependencies
pipenv install -d
```

To run the tools

```bash
# Sort imports
isort .

# Format
black .

# Lint
pylint gcfpack

# Validate typing
mypy gcfpack
```

### Testing

To run the tests:

```bash
pytest test
```

To get a coverage report, run:

```bash
pytest --cov=gcfpack test
```

### Documentation

gcfpack's documentation is built via Sphinx. To build the documentation, run:

```bash
# Generate the API docs from the Python source code
sphinx-apidoc -f --ext-autodoc -o doc gcfpack

# Build the HTML documentation
sphinx-build -a -b html doc dist/doc
```

## License

Usage and distribution of this application is subject to the [MIT License](./LICENSE).

## Bugs, feedback and suggestions

For bugs, feedback and suggestions, create a new issue on the [issue tracker](https://github.com/global-container-format/gcfpack/issues).
