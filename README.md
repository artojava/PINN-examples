# Python code examples

This directory contains code examples written in Python for the Physics-Informed Neural Networks (PINNs) framework. The examples are organized in the `notebook` subdirectory based on the type of problem being solved.

## Setting up the python environment

For the management of the Python environment it is recommended to use `uv`. Installation instructions can be found at [uv's website](https://docs.astral.sh/uv/).

After installing `uv`, create a new virtual environment as follows:

```bash
uv venv .venv
```

Then, activate the virtual environment:

```bash
source .venv/bin/activate
```

In Windows, use the following command to activate the virtual environment:

```bash
.venv\Scripts\activate
```

Next, install the required packages using `pip`:

```bash
uv pip install -r requirements.txt
```