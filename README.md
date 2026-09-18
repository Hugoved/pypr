# pypr

**pypr** is a Python utility for working with PlayReady devices, headers, PSSH data, and local CDM workflows.

It supports PlayReady device files, device creation and export, license testing, inspection tools, and PlayReady header generation.

---

## Features

- Load and inspect PlayReady device files
- Create and build PlayReady devices
- Export device components
- Reprovision supported devices
- Parse PlayReady PSSH and WRM headers
- Generate PlayReady headers
- Generate license challenges
- Parse license responses
- Test PlayReady devices
- Single-file Python implementation
- No persistent application storage required

---

## Requirements

- Python 3.9+
- `pycryptodome`
- `ecpy`
- `requests`

Install:

```bash
pip install pycryptodome ecpy requests
```

---

## Usage

```bash
python pypr.py <command> [options]
```

Available commands include:

```text
license
test
create-device
build-device
reprovision-device
inspect
export-device
serve
header
```

Use:

```bash
python pypr.py --help
```

or:

```bash
python pypr.py <command> --help
```

for command-specific options.

---

## Test

Test a PlayReady device:

```bash
python pypr.py test device.prd
```

---

## License

Run a license request using a PlayReady device:

```bash
python pypr.py license --help
```

---

## Create Device

Create a PlayReady device from a group certificate and group key:

```bash
python pypr.py create-device -c bgroupcert.dat -k zgpriv.dat
```

Optional encryption and signing keys can also be supplied:

```bash
python pypr.py create-device -c bgroupcert.dat -k zgpriv.dat -e zprivencr.dat -s zprivsig.dat
```

A protected group key can be used with `-pk` instead of `-k`.


---

## Build Device

Build a PlayReady device from a certificate, encryption key, and signing key:

```bash
python pypr.py build-device -c bgroupcert.dat -e zprivencr.dat -s zgpriv.dat
```

Optional output:

```bash
python pypr.py build-device -c bgroupcert.dat -e zprivencr.dat -s zgpriv.dat -o device.prd
```

Use `--overwrite` if the output file already exists.


---

## Inspect

Inspect a PlayReady device or supported PlayReady structure:

```bash
python pypr.py inspect --help
```

---

## Export Device

Export components from a PlayReady device:

```bash
python pypr.py export-device --help
```

---

## Header

Create a PlayReady header from a KID:

```bash
python pypr.py header 00000000000000000000000000000000
```

Additional header options are available through:

```bash
python pypr.py header --help
```

---

## Python Usage

### Load a Device

```python
from pypr import Device

device = Device.load("device.prd")
```

### PlayReady Header Builder

```python
import base64
from pypr import PlayReadyHeaderBuilder

kid = "00000000000000000000000000000000"

builder = PlayReadyHeaderBuilder(kid)

header = builder.build_header(
    version="4.0",
    header_spec=None,
    encryption_scheme="cenc",
    key_specs=[(kid, kid)],
)

print(base64.b64encode(header).decode())
```

### PSSH

```python
from pypr import PSSH

pssh = PSSH("BASE64_PSSH")

print(pssh.wrm_headers)
```

---

## Notes

- PlayReady device files use the `.prd` extension.
- The tool can be used from both the command line and Python.
- Device building supports certificate, encryption-key, and signing-key files.
- PlayReady header generation is available through both Python and the `header` command.

---

## Disclaimer

This tool is intended for educational, research, interoperability, and authorized testing purposes.

Use it only with devices, services, and content that you are authorized to access.

---

## Acknowledgements

The project is inspired by pyplayready and adapted into a standalone Python implementation.
