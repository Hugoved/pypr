# pypr

**pypr** is a Python toolkit for parsing, analyzing, and interacting with **Microsoft PlayReady (PRD) device files**, PlayReady headers, PSSH data, and license acquisition workflows.

It provides structured, low-level access to PlayReady internals, enabling controlled inspection of device credentials, WRMHEADER data, SOAP-based license exchanges, and content key extraction.

---

## Overview

`pypr` offers a standalone and modular implementation of PlayReady workflows, inspired by established projects such as **pyplayready** and **Bento4**. The project emphasizes clarity, extensibility, and direct control over DRM-related structures.

It is intended for research, interoperability testing, and technical analysis of PlayReady-protected content.

---

## Features

* Parsing and loading of **PlayReady Device (PRD) files**
* Device initialization from:

  * PRD files
  * Exported certificate (`bgroupcert.dat`)
  * Private key (`zgpriv.dat`)
* Parsing and decoding of **PlayReady PSSH** containers
* Extraction and processing of **WRMHEADER** data
* Generation of **license acquisition challenges** (SOAP/XML)
* Parsing of **license responses**
* Extraction of **content keys (KID / KEY pairs)**
* Support for **Revocation Lists** in license requests
* Creation and customization of **PlayReady headers**
* Integration with required cryptographic primitives

---

## Requirements

* Python 3.9 or higher
* `pycryptodome`
* `construct==2.8.8`
* `lxml`
* `requests`

Install dependencies:

```bash
pip install pycryptodome construct==2.8.8 lxml requests
```

> **Note:** This project is specifically tested with `construct==2.8.8`. Newer versions may introduce breaking changes.

---

## Usage

```bash
python pypr.py [options]
```

---

## Examples

### Using Exported Device Files

```python
import requests
from pypr import PSSH, Device, Cdm, RevocationList

device = Device.from_files(
    certificate="bgroupcert.dat",
    key="zgpriv.dat",
)

cdm = Cdm.from_device(device)
session_id = cdm.open()

pssh = PSSH("AAADfHBzc2gAAAAAmgTweZhAQoarkuZb4IhflQAAA1xcAwAAAQABAFIDPABXAFIATQBIAEUAQQBEAEUAUgAgAHgAbQBsAG4AcwA9"
            "ACIAaAB0AHQAcAA6AC8ALwBzAGMAaABlAG0AYQBzAC4AbQBpAGMAcgBvAHMAbwBmAHQALgBjAG8AbQAvAEQAUgBNAC8AMgAwADAA"
            "NwAvADAAMwAvAFAAbABhAHkAUgBlAGEAZAB5AEgAZQBhAGQAZQByACIAIAB2AGUAcgBzAGkAbwBuAD0AIgA0AC4AMAAuADAALgAw"
            "ACIAPgA8AEQAQQBUAEEAPgA8AFAAUgBPAFQARQBDAFQASQBOAEYATwA+ADwASwBFAFkATABFAE4APgAxADYAPAAvAEsARQBZAEwA"
            "RQBOAD4APABBAEwARwBJAEQAPgBBAEUAUwBDAFQAUgA8AC8AQQBMAEcASQBEAD4APAAvAFAAUgBPAFQARQBDAFQASQBOAEYATwA+"
            "ADwASwBJAEQAPgA0AFIAcABsAGIAKwBUAGIATgBFAFMAOAB0AEcAawBOAEYAVwBUAEUASABBAD0APQA8AC8ASwBJAEQAPgA8AEMA"
            "SABFAEMASwBTAFUATQA+AEsATABqADMAUQB6AFEAUAAvAE4AQQA9ADwALwBDAEgARQBDAEsAUwBVAE0APgA8AEwAQQBfAFUAUgBMAD4AaAB0AHQAcABzADoALwAvAHAAcgBvAGYAZgBpAGMAaQBhAGwAcwBpAHQAZQAuAGsAZQB5AGQAZQBsAGkAdgBlAHIAeQAuAG0AZQBkAGkAYQBzAGUAcgB2AGkAYwBlAHMALgB3AGkAbgBkAG8AdwBzAC4AbgBlAHQALwBQAGwAYQB5AFIAZQBhAGQAeQAvADwALwBMAEEAXwBVAFIATAA+ADwAQwBVAFMAVABPAE0AQQBUAFQAUgBJAEIAVQBUAEUAUwA+ADwASQBJAFMAXwBEAFIATQBfAFYARQBSAFMASQBPAE4APgA4AC4AMQAuADIAMwAwADQALgAzADEAPAAvAEkASQBTAF8ARABSAE0AXwBWAEUAUgBTAEkATwBOAD4APAAvAEMAVQBTAFQATwBNAEEAVABUAFIASQBCAFUAVABFAFMAPgA8AC8ARABBAFQAQQA+ADwALwBXAFIATQBIAEUAQQBEAEUAUgA+AA==")

try:
    request = cdm.get_license_challenge(
        session_id,
        pssh.wrm_headers[0],
        rev_lists=RevocationList.SupportedListIds,
    )

    response = requests.post(
        url="https://test.playready.microsoft.com/service/rightsmanager.asmx?cfg=(persist:false,sl:2000)",
        headers={"Content-Type": "text/xml; charset=UTF-8"},
        data=request,
    )

    response.raise_for_status()

    cdm.parse_license(session_id, response.text)

    for key in cdm.get_keys(session_id):
        print(f"{key.key_id.hex}:{key.key.hex()}")

finally:
    cdm.close(session_id)
```

---

### Using a PRD Device File

```python
import requests
from pypr import PSSH, Device, Cdm, RevocationList

device = Device.load("funai_electric_tv_43pfl4901f8_sl2000.prd")

cdm = Cdm.from_device(device)
session_id = cdm.open()

pssh = PSSH("AAADfHBzc2gAAAAAmgTweZhAQoarkuZb4IhflQAAA1xcAwAAAQABAFIDPABXAFIATQBIAEUAQQBEAEUAUgAgAHgAbQBsAG4AcwA9"
            "ACIAaAB0AHQAcAA6AC8ALwBzAGMAaABlAG0AYQBzAC4AbQBpAGMAcgBvAHMAbwBmAHQALgBjAG8AbQAvAEQAUgBNAC8AMgAwADAA"
            "NwAvADAAMwAvAFAAbABhAHkAUgBlAGEAZAB5AEgAZQBhAGQAZQByACIAIAB2AGUAcgBzAGkAbwBuAD0AIgA0AC4AMAAuADAALgAw"
            "ACIAPgA8AEQAQQBUAEEAPgA8AFAAUgBPAFQARQBDAFQASQBOAEYATwA+ADwASwBFAFkATABFAE4APgAxADYAPAAvAEsARQBZAEwA"
            "RQBOAD4APABBAEwARwBJAEQAPgBBAEUAUwBDAFQAUgA8AC8AQQBMAEcASQBEAD4APAAvAFAAUgBPAFQARQBDAFQASQBOAEYATwA+"
            "ADwASwBJAEQAPgA0AFIAcABsAGIAKwBUAGIATgBFAFMAOAB0AEcAawBOAEYAVwBUAEUASABBAD0APQA8AC8ASwBJAEQAPgA8AEMA"
            "SABFAEMASwBTAFUATQA+AEsATABqADMAUQB6AFEAUAAvAE4AQQA9ADwALwBDAEgARQBDAEsAUwBVAE0APgA8AEwAQQBfAFUAUgBMAD4AaAB0AHQAcABzADoALwAvAHAAcgBvAGYAZgBpAGMAaQBhAGwAcwBpAHQAZQAuAGsAZQB5AGQAZQBsAGkAdgBlAHIAeQAuAG0AZQBkAGkAYQBzAGUAcgB2AGkAYwBlAHMALgB3AGkAbgBkAG8AdwBzAC4AbgBlAHQALwBQAGwAYQB5AFIAZQBhAGQAeQAvADwALwBMAEEAXwBVAFIATAA+ADwAQwBVAFMAVABPAE0AQQBUAFQAUgBJAEIAVQBUAEUAUwA+ADwASQBJAFMAXwBEAFIATQBfAFYARQBSAFMASQBPAE4APgA4AC4AMQAuADIAMwAwADQALgAzADEAPAAvAEkASQBTAF8ARABSAE0AXwBWAEUAUgBTAEkATwBOAD4APAAvAEMAVQBTAFQATwBNAEEAVABUAFIASQBCAFUAVABFAFMAPgA8AC8ARABBAFQAQQA+ADwALwBXAFIATQBIAEUAQQBEAEUAUgA+AA==")

try:
    request = cdm.get_license_challenge(
        session_id,
        pssh.wrm_headers[0],
        rev_lists=RevocationList.SupportedListIds,
    )

    response = requests.post(
        url="https://test.playready.microsoft.com/service/rightsmanager.asmx?cfg=(persist:false,sl:2000)",
        headers={"Content-Type": "text/xml; charset=UTF-8"},
        data=request,
    )

    response.raise_for_status()

    cdm.parse_license(session_id, response.text)

    for key in cdm.get_keys(session_id):
        print(f"{key.key_id.hex}:{key.key.hex()}")

finally:
    cdm.close(session_id)
```

---

### Building a PlayReady Header

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

print("PlayReady Header:", base64.b64encode(header).decode())
```

---

### Creating a PlayReady Header from KID

```python
from pypr import create_playready_header_from_kid

kid = "00000000000000000000000000000000"

header = create_playready_header_from_kid(
    kid=kid,
    key=kid,
    version="4.0",
    encryption_scheme="cenc",
)

print("PlayReady Header:", header)
```

---

## Architecture

The project is structured into distinct layers:

* **Device Layer**
  Handles PRD parsing and credential loading (certificate chain and private key)

* **CDM Layer**
  Manages session lifecycle, challenge generation, and license parsing

* **PSSH Layer**
  Extracts WRMHEADER and initialization data

* **License Workflow**

  1. Parse PSSH and extract WRMHEADER
  2. Generate license challenge (SOAP/XML)
  3. Send request to license server
  4. Parse license response
  5. Extract content keys

---

## Disclaimer

This tool is intended strictly for **educational, research, and interoperability purposes**.
The author does not support or encourage the misuse of DRM systems or unauthorized access to protected content.

---

## Issues and Support

For bug reports, feature requests, or general inquiries, please open an issue in the repository.

Support and updates are provided as availability permits.

---

## Acknowledgements

This project is based on **pyplayready** and **Bento4**, drawing inspiration from their implementations and design approaches.
