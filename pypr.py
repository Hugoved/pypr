from __future__ import annotations
import argparse
import base64
import binascii
import json
import logging
import os
import re
import shutil
import struct
import sys
import time
from dataclasses import dataclass
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Optional, Union
from uuid import UUID

__version__ = "1.9.0"

class PlayReadyException(Exception):
    """Exceptions used by """

class TooManySessions(PlayReadyException):
    """Too many Sessions are open."""

class InvalidSession(PlayReadyException):
    """No Session is open with the specified identifier."""

class InvalidSoapMessage(PlayReadyException):
    """The Soap Message is invalid or empty."""

class InvalidPssh(PlayReadyException):
    """The Playready PSSH is invalid or empty."""

class InvalidWrmHeader(PlayReadyException):
    """The Playready WRMHEADER is invalid or empty."""

class InvalidChecksum(PlayReadyException):
    """The Playready WRMHEADER key ID checksum is invalid or empty."""

class InvalidInitData(PlayReadyException):
    """The Playready Cenc Header Data is invalid or empty."""

class DeviceMismatch(PlayReadyException):
    """The Remote CDMs Device information and the APIs Device information did not match."""

class InvalidXmrLicense(PlayReadyException):
    """Unable to parse XMR License."""

class InvalidLicense(PlayReadyException):
    """Unable to parse License XML."""

class InvalidCertificate(PlayReadyException):
    """The BCert is not correctly formatted."""

class InvalidCertificateChain(PlayReadyException):
    """The BCertChain is not correctly formatted."""

class OutdatedDevice(PlayReadyException):
    """The PlayReady Device is outdated and does not support a specific operation."""

class ServerException(PlayReadyException):
    """Re-casted on the client if found in license response."""

class InvalidRevocationList(PlayReadyException):
    """The RevocationList is not correctly formatted."""

from enum import Enum

class DrmResult(Enum):
    DRM_SUCCESS = (0x00000000, "Operation was successful.")
    DRM_S_FALSE = (0x00000001, "Operation was successful, but returned a FALSE test condition.")
    DRM_S_MORE_DATA = (0x00000002, "Operation was successful, but more data is available.")
    DRM_S_TEST_SKIP_FILE = (0x0004C300, "Skip processing this file, not an eror.")
    DRM_S_TEST_CONVERTED_FILE = (0x0004C301, "The file was converted to a PlayReady file during the action.")
    DRM_E_OEM_CONSTRAINT_1_FAIL = (0x8004DFF, "Failed while OEM CONSTRAINT-1 check")
    DRM_E_OEM_CONSTRAINT_2_FAIL = (0x8004DFF, "Failed while OEM CONSTRAINT-2 check")
    DRM_E_OEM_CONSTRAINT_3_FAIL = (0x8004DFF, "Failed while OEM CONSTRAINT-3 check")
    DRM_E_HDCP_NON_SECURE = (0x8004DFF, "Attempt to play back through insecure HDMI output path")
    DRM_E_OUTOFMEMORY = (0x80000002, "Insufficient resources exist to complete the request.")
    DRM_E_NOTIMPL = (0x80004001, "The requested operation is not implemented.")
    DRM_E_POINTER = (0x80004003, "Invalid pointer.")
    DRM_E_FAIL = (0x80004005, "The requested operation failed.")
    DRM_E_HLOS_TAMPERED = (0x80004006, "HLOS tampered.")
    DRM_E_OPL_BLOCKED = (0x80004007, "OPL blocked.")
    DRM_E_LOAD_IMG = (0x80004008, "Failed on loading playready image.")
    DRM_E_VER_MISMATCH = (0x80004009, "Version mismatch between HLOS and TZ.")
    DRM_E_SET_BANDWIDTH = (0x8000400A, "Failed on setting bandwidth.")
    DRM_E_OUT_OF_BOUND = (0x8000400B, "Out of bound.")
    DRM_E_PLAY_ENABLER_BLOCKED = (0x8000400C, "WFD is blocked as play enabler object for HDCP doesn't exist in license")
    DRM_E_HDMI_READ_FAIL = (0x8000400E, "Failed to read HDMI Status")
    DRM_E_FILENOTFOUND = (0x80030002, "A requested file could not be found.")
    DRM_E_FILEOPEN = (0x8003006E, "A request failed due to a file being open.")
    DRM_E_VERIFICATION_FAILURE = (0x80040E80, "Validation of a Longhorn certificate failed.")
    DRM_E_RSA_SIGNATURE_ERROR = (0x80040E82, "Error in RSA(PSS) signature.")
    DRM_E_BAD_RSA_EXPONENT = (0x80040E86, "An incorrect RSA exponent was supplied for a public key.")
    DRM_E_P256_CONVERSION_FAILURE = (0x80040E87, "An error occurred while converting between P256 types.")
    DRM_E_P256_PKCRYPTO_FAILURE = (0x80040E88, "An error occurred in an asymmetric P256 cryptographic operation.")
    DRM_E_P256_PLAINTEXT_MAPPING_FAILURE = (0x80040E89, "An error occurred while attempting to map a plaintext array to a EC Point: There is no conversion for this byte array to a EC Point.")
    DRM_E_P256_INVALID_SIGNATURE = (0x80040E8A, "The ECDSA signature to be verified was not a valid signature format.")
    DRM_E_P256_ECDSA_VERIFICATION_ERROR = (0x80040E8B, "The ECDSA verification algorithm encountered an unknown error.")
    DRM_E_P256_ECDSA_SIGNING_ERROR = (0x80040E8C, "The ECDSA signature algorithm encountered an unknown error.")
    DRM_E_P256_HMAC_KEYGEN_FAILURE = (0x80040E8D, "Could not generate a valid HMAC key under constraint where CK || HMACK is a valid x coord on the EC (P256).")
    DRM_E_CH_VERSION_MISSING = (0x80041103, "Missing content header version.")
    DRM_E_CH_KID_MISSING = (0x80041104, "Missing KID attribute in content header.")
    DRM_E_CH_LAINFO_MISSING = (0x80041105, "Missing LAINFO attribute in content header.")
    DRM_E_CH_CHECKSUM_MISSING = (0x80041106, "Missing content header checksum.")
    DRM_E_CH_ATTR_MISSING = (0x80041107, "Missing content header attribute.")
    DRM_E_CH_INVALID_HEADER = (0x80041108, "Invalid content header.")
    DRM_E_CH_INVALID_CHECKSUM = (0x80041109, "Invalid checksum in the header.")
    DRM_E_CH_UNABLE_TO_VERIFY = (0x8004110A, "Unable to verify signature of content header.")
    DRM_E_CH_UNSUPPORTED_VERSION = (0x8004110B, "Unsupported content header version.")
    DRM_E_CH_UNSUPPORTED_HASH_ALGORITHM = (0x8004110C, "Unsupported hash algorithm.")
    DRM_E_CH_UNSUPPORTED_SIGN_ALGORITHM = (0x8004110D, "Unsupported signature algorithm.")
    DRM_E_CH_BAD_KEY = (0x8004110E, "Invalid key.")
    DRM_E_CH_INCOMPATIBLE_HEADER_TYPE = (0x8004110F, "Incompatible content header type.")
    DRM_E_HEADER_ALREADY_SET = (0x80041110, "Content header type is already set. Reinitialize is required.")
    DRM_E_CH_MULTIPLE_KIDS = (0x80041111, "Content header includes multiple KIDs.  The operation requested is unsupported.")
    DRM_E_CH_NOT_SIGNED = (0x80041113, "The header was not signed.")
    DRM_E_CH_UNKNOWN_ERROR = (0x80041116, "Unknown Error.")
    DRM_E_CDMIGRATIONTOOL_INVALID_FILE = (0x80041180, "File cannot be migrated because it is invalid.")
    DRM_E_CDMIGRATIONTOOL_FILE_IS_NOT_CD_RIPPED = (0x80041181, "File cannot be migrated because it was not ripped from CD.")
    DRM_E_CDMIGRATIONTOOL_FILE_IS_NOT_PROTECTED = (0x80041182, "File cannot be migrated because it is not protected.")
    DRM_E_CDMIGRATIONTOOL_LICENSE_KID_INVALID = (0x80041183, "File cannot be migrated because the server returned a license with an invalid KID.")
    DRM_E_CDMIGRATIONTOOL_LICENSE_KID_MISMATCH = (0x80041184, "File cannot be migrated because the server returned a license with a KID that did not match the content.")
    DRM_E_CDMIGRATIONTOOL_LICENSE_CONTENT_KEY_INVALID = (0x80041185, "File cannot be migrated because the server returned a license with an invalid content key.")
    DRM_E_CDMIGRATIONTOOL_INVALID_ASF_FORMAT = (0x80041186, "File cannot be migrated because the ASF is corrupt.")
    DRM_E_CDMIGRATIONTOOL_INVALID_ASF_PACKETS = (0x80041187, "File cannot be migrated because the ASF packets are corrupt.")
    DRM_E_CDMIGRATIONTOOL_CONTENT_KEY_CACHE_CORRUPT = (0x80041188, "File cannot be migrated because the content key obtained from the local cache is invalid.")
    DRM_E_CDMIGRATIONTOOL_FILE_WRITE_ERROR = (0x80041189, "File cannot be migrated because the file could not be written.")
    DRM_E_CDMIGRATIONTOOL_CANCELLED = (0x8004118A, "File migration was cancelled.")
    LIC_INIT_FAILURE = (0x80041201, "LIC_INIT_FAILURE")
    LIC_LICENSE_NOTSET = (0x80041202, "LIC_LICENSE_NOTSET")
    LIC_PARAM_NOT_OPTIONAL = (0x80041203, "LIC_PARAM_NOT_OPTIONAL")
    LIC_MEMORY_ALLOCATION_ERROR = (0x80041204, "LIC_MEMORY_ALLOCATION_ERROR")
    LIC_INVALID_LICENSE = (0x80041205, "LIC_INVALID_LICENSE")
    LIC_FIELD_MISSING = (0x80041206, "LIC_FIELD_MISSING")
    DRM_E_LIC_UNSUPPORTED_VALUE = (0x80041207, " DRM_E_LIC_UNSUPPORTED_VALUE")
    LIC_UNKNOWN_ERROR = (0x80041208, "LIC_UNKNOWN_ERROR")
    LIC_INVALID_REVLIST = (0x80041209, "LIC_INVALID_REVLIST")
    LIC_EXPIRED_CERT = (0x8004120A, "LIC_EXPIRED_CERT")
    DRM_E_CDMI_INVALID_INITIALIZATION_DATA = (0x80041301, "Invalid initialization data.")
    DRM_E_CDMI_PERSISTENT_LICENSE_FOR_NON_PERSISTENT_LICENSE_SESSION = (0x80041302, "A persistent license was provided for a session that was not persistent-license.")
    DRM_E_CDMI_SECURE_STOP_LICENSE_FOR_NON_PERSISTENT_USAGE_RECORD_SESSION = (0x80041303, "A secure stop license was provided for a session that was not persistent-usage-record.")
    DRM_E_CDMI_TEMPORARY_LICENSE_FOR_NON_TEMPORARY_SESSION = (0x80041304, "An in-memory-only license without secure-stop was provided for a session that was not temporary.")
    DRM_E_CDMI_UNSUPPORTED_KEY_SYSTEM = (0x80041305, "The requested key system is not supported by PlayReady.")
    DRM_E_CDMI_UNSUPPORTED_INITIALIZATION_DATA_TYPES = (0x80041306, "None of the requested initialization data types are supported by PlayReady.")
    DRM_E_CDMI_UNSUPPORTED_DISTINCTIVE_IDENTIFIER = (0x80041307, "The requested distinctive identifier setting is not supported by PlayReady.")
    DRM_E_CDMI_UNSUPPORTED_SESSION_TYPE = (0x80041308, "The requested session type is not supported by PlayReady.")
    DRM_E_CDMI_UNSUPPORTED_INITIALIZATION_DATA = (0x80041309, "The provided initialization data is not supported by PlayReady.")
    DRM_E_CDMI_SESSION_ALREADY_USED = (0x8004130A, "The session has already been used.")
    DRM_E_CDMI_SESSION_UNINITIALIZED = (0x8004130B, "The session is not yet initialized.")
    DRM_E_CDMI_SESSION_CLOSED = (0x8004130C, "The session is closed.")
    DRM_E_CDMI_SESSION_ID_NOT_FOUND = (0x8004130D, "The given session ID could not be found.")
    DRM_E_CDMI_SESSION_TYPE_MISMATCH = (0x8004130E, "The given session was initialized with a different session type than the session being loaded or Load/Remove was called on a temporary session.")
    DRM_E_CDMI_SECURE_STOP_LICENSE_FOR_NON_PERSISTENT_USAGE_RECORD_SESSION_2 = (0x8004130F, "A secure stop license was provided for a session that was not persistent-usage-record.")
    DRM_E_CPRMEXP_NOERROR = (0x80041400, "DRM_E_CPRMEXP_NOERROR")
    CPRMEXP_PARAM_NOT_OPTIONAL = (0x80041401, "CPRMEXP_PARAM_NOT_OPTIONAL")
    CPRMEXP_MEMORY_ALLOCATION_ERROR = (0x80041402, "CPRMEXP_MEMORY_ALLOCATION_ERROR")
    CPRMEXP_NO_OPERANDS_IN_EXPRESSION = (0x80041403, "CPRMEXP_NO_OPERANDS_IN_EXPRESSION")
    CPRMEXP_INVALID_TOKEN = (0x80041404, "CPRMEXP_INVALID_TOKEN")
    CPRMEXP_INVALID_CONSTANT = (0x80041405, "CPRMEXP_INVALID_CONSTANT")
    CPRMEXP_INVALID_VARIABLE = (0x80041406, "CPRMEXP_INVALID_VARIABLE")
    CPRMEXP_INVALID_FUNCTION = (0x80041407, "CPRMEXP_INVALID_FUNCTION")
    CPRMEXP_INVALID_ARGUMENT = (0x80041408, "CPRMEXP_INVALID_ARGUMENT")
    CPRMEXP_INVALID_CONTEXT = (0x80041409, "CPRMEXP_INVALID_CONTEXT")
    CPRMEXP_ENDOFBUFFER = (0x8004140A, "CPRMEXP_ENDOFBUFFER")
    CPRMEXP_MISSING_OPERAND = (0x8004140B, "CPRMEXP_MISSING_OPERAND")
    CPRMEXP_OVERFLOW = (0x8004140C, "CPRMEXP_OVERFLOW")
    CPRMEXP_UNDERFLOW = (0x8004140D, "CPRMEXP_UNDERFLOW")
    CPRMEXP_INCORRECT_NUM_ARGS = (0x8004140E, "CPRMEXP_INCORRECT_NUM_ARGS")
    CPRMEXP_VARIABLE_EXPECTED = (0x8004140F, "CPRMEXP_VARIABLE_EXPECTED")
    CPRMEXP_RETRIEVAL_FAILURE = (0x80041410, "CPRMEXP_RETRIEVAL_FAILURE")
    CPRMEXP_UPDATE_FAILURE = (0x80041411, "CPRMEXP_UPDATE_FAILURE")
    CPRMEXP_STRING_UNTERMINATED = (0x80041412, "CPRMEXP_STRING_UNTERMINATED")
    CPRMEXP_UPDATE_UNSUPPORTED = (0x80041413, "CPRMEXP_UPDATE_UNSUPPORTED")
    CPRMEXP_ISOLATED_OPERAND_OR_OPERATOR = (0x80041414, "CPRMEXP_ISOLATED_OPERAND_OR_OPERATOR")
    CPRMEXP_UNMATCHED = (0x80041415, "CPRMEXP_UNMATCHED")
    CPRMEXP_WRONG_TYPE_OPERAND = (0x80041416, "CPRMEXP_WRONG_TYPE_OPERAND")
    CPRMEXP_TOO_MANY_OPERANDS = (0x80041417, "CPRMEXP_TOO_MANY_OPERANDS")
    CPRMEXP_UNKNOWN_PARSE_ERROR = (0x80041418, "CPRMEXP_UNKNOWN_PARSE_ERROR")
    CPRMEXP_UNSUPPORTED_FUNCTION = (0x80041419, "CPRMEXP_UNSUPPORTED_FUNCTION")
    CPRMEXP_CLOCK_REQUIRED = (0x8004141A, "CPRMEXP_CLOCK_REQUIRED")
    DRM_E_LIC_KEY_DECODE_FAILURE = (0x80048007, "Key decode failure.")
    DRM_E_LIC_SIGNATURE_FAILURE = (0x80048008, "License signature failure.")
    DRM_E_LIC_KEY_AND_CERT_MISMATCH = (0x80048013, "Key and cert mismatch.")
    DRM_E_KEY_MISMATCH = (0x80048014, "A public/private keypair is mismatched.")
    DRM_E_INVALID_SIGNATURE = (0x800480CF, "License signature failure.")
    DRM_E_SYNC_ENTRYNOTFOUND = (0x800480D0, "An entry was not found in the sync store.")
    DRM_E_STACKTOOSMALL = (0x800480D1, "The stack supplied to the DRM API was too small.")
    DRM_E_CIPHER_NOT_INITIALIZED = (0x800480D2, "The DRM Cipher routines were not correctly initialized before calling encryption/decryption routines.")
    DRM_E_DECRYPT_NOT_INITIALIZED = (0x800480D3, "The DRM decrypt routines were not correctly initialized before trying to decrypt data.")
    DRM_E_SECURESTORE_LOCK_NOT_OBTAINED = (0x800480D4, "Before reading or writing data to securestore in raw mode, first the lock must be obtained using DRM_SST_OpenData.")
    DRM_E_PKCRYPTO_FAILURE = (0x800480D5, "An error occurred in an asymmetric cryptographic operation.")
    DRM_E_INVALID_DST_SLOT_SIZE = (0x800480D6, "Invalid DST slot size is specified.")
    DRM_E_UNSUPPORTED_VERSION = (0x80049005, " DRM_E_UNSUPPORTED_VERSION")
    DRMUTIL_EXPIRED_CERT = (0x80049006, "DRMUTIL_EXPIRED_CERT")
    DRMUTIL_INVALID_CERT = (0x80049007, "DRMUTIL_INVALID_CERT")
    DRM_E_DEVICE_NOT_REGISTERED = (0x8004A000, "The DEVICEID does not exist in the device store")
    DRM_E_TOO_MANY_INCLUSION_GUIDS = (0x8004A001, "The license contained more than DRM_MAX_INCLUSION_GUIDS entries in its inclusion list")
    DRM_E_REVOCATION_GUID_NOT_RECOGNIZED = (0x8004A002, "The revocation list type GUID was not recognized")
    DRM_E_LIC_CHAIN_TOO_DEEP = (0x8004A003, "The license chained deeper than this implementation can handle")
    DRM_E_DEVICE_SECURITY_LEVEL_TOO_LOW = (0x8004A004, "The security level of the remote device is too low to receive the license")
    DRM_E_DST_BLOCK_CACHE_CORRUPT = (0x8004A005, "The block header cache returned invalid data")
    DRM_E_CONTRACT_FAILED = (0x8004A006, "The error code returned by the API is not present in the contract")
    DRM_E_DST_BLOCK_CACHE_MISS = (0x8004A007, "The block header cache didn't contain the requested block header")
    DRM_E_INVALID_METERRESPONSE_SIGNATURE = (0x8004A013, "Invalid signature in meter response")
    DRM_E_INVALID_LICENSE_REVOCATION_LIST_SIGNATURE = (0x8004A014, "Invalid signature in license revocation list.")
    DRM_E_INVALID_METERCERT_SIGNATURE = (0x8004A015, "Invalid signature in metering certificate")
    DRM_E_METERSTORE_DATA_NOT_FOUND = (0x8004A016, "Metering data slot not found due to bad data in response file")
    DRM_E_NO_LICENSES_TO_SYNC = (0x8004A017, "No more licenses to sync")
    DRM_E_INVALID_REVOCATION_LIST = (0x8004A018, "The revocation list version does not match the current revocation version")
    DRM_E_ENVELOPE_CORRUPT = (0x8004A019, "The envelope archive or file is corrupt")
    DRM_E_ENVELOPE_FILE_NOT_COMPATIBLE = (0x8004A01A, "The envelope file is not compatible with this version of the porting kit")
    DRM_E_EXTENDED_RESTRICTION_NOT_UNDERSTOOD = (0x8004A01B, "An extensible restriction was not understood by the app, and is mark as being required")
    DRM_E_INVALID_SLK = (0x8004A01C, "An ILA SLK (symmetric session key) was found, but did not contain valid data")
    DRM_E_DEVCERT_MODEL_MISMATCH = (0x8004A01D, "The model string in the certificate does not match the model of the device and so the cert must be re-generated.")
    DRM_E_OUTDATED_REVOCATION_LIST = (0x8004A01E, "The revocation list is outdated. It is required for the revocation list to be refreshed at least every 90 days.")
    DRM_E_DSTR_NOT_FOUND = (0x8004A01F, "The substring search inside a DRM string failed.")
    DRM_E_DEVICE_NOT_INITIALIZED = (0x8004C001, "This device has not been initialized against a DRM init service")
    DRM_E_DRM_NOT_INITIALIZED = (0x8004C002, "The app has not call DRM_Init properly")
    DRM_E_INVALIDRIGHT = (0x8004C003, "A right in the license in invalid")
    DRM_E_INCOMPATABLELICENSESIZE = (0x8004C004, "The size of the license is incompatable. DRM doesn't understand this license")
    DRM_E_INVALIDLICENSEFLAGS = (0x8004C005, "The flags in the license are invalid. DRM either doesn't understand them or they are conflicting")
    DRM_E_INVALID_LICENSE = (0x8004C006, "The license is invalid")
    DRM_E_CONDITIONFAIL = (0x8004C007, "A condition in the license failed to pass")
    DRM_E_CONDITIONNOTSUPPORTED = (0x8004C008, "A condition in the license is not supported by this verison of DRM")
    DRM_E_LICENSE_EXPIRED = (0x8004C009, "The license has expired either by depleting a play count or via an end time.")
    DRM_E_LICENSENOTYETVALID = (0x8004C00A, "The license start time had not come to pass yet.")
    DRM_E_RIGHTS_NOT_AVAILABLE = (0x8004C00B, "The rights the app has requested are not available in the license")
    DRM_E_LICENSEMISMATCH = (0x8004C00C, "The license content id/ sku id doesn't match that requested by the app")
    DRM_E_WRONG_PARAMETER_TYPE = (0x8004C00D, "The token parameter was of an incompatible type.")
    DRM_E_NORIGHTSREQUESTED = (0x8004C00E, "The app has not requested any rights before trying to bind")
    DRM_E_LICENSE_NOT_BOUND = (0x8004C00F, "A license has not been bound to. Decrypt can not happen without a successful bind call")
    DRM_E_HASH_MISMATCH = (0x8004C010, "A Keyed Hash check failed.")
    DRM_E_INVALIDTIME = (0x8004C011, "A time structure is invalid.")
    DRM_E_LICENSESTORENOTFOUND = (0x8004C012, "The external license store was not found.")
    DRM_E_LICENSE_NOT_FOUND = (0x8004C013, "A license was not found in the license store.")
    DRM_E_LICENSE_VERSION_NOT_SUPPORTED = (0x8004C014, "The DRM license version is not supported by the DRM version on the device.")
    DRM_E_INVALIDBINDID = (0x8004C015, "The bind id is invalid.")
    DRM_E_UNSUPPORTED_ALGORITHM = (0x8004C016, "The encryption algorithm required for this operation is not supported.")
    DRM_E_ALGORITHMNOTSET = (0x8004C017, "The encryption algorithm required for this operation is not supported.")
    DRM_E_LICENSESERVERNEEDSKEY = (0x8004C018, "The license server needs a version of the device bind key from the init service.")
    DRM_E_INVALID_LICENSE_STORE = (0x8004C019, "The license store version number is incorrect, or the store is invalid in some other way.")
    DRM_E_FILE_READ_ERROR = (0x8004C01A, "There was an error reading a file.")
    DRM_E_FILE_WRITE_ERROR = (0x8004C01B, "There was an error writing a file.")
    DRM_E_CLIENTTIMEINVALID = (0x8004C01C, "The time/clock on the device is not in sync with the license server within tolerance.")
    DRM_E_DST_STORE_FULL = (0x8004C01D, "The data store is full.")
    DRM_E_NO_XML_OPEN_TAG = (0x8004C01E, "XML open tag not found")
    DRM_E_NO_XML_CLOSE_TAG = (0x8004C01F, "XML close tag not found")
    DRM_E_INVALID_XML_TAG = (0x8004C020, "Invalid XML tag")
    DRM_E_NO_XML_CDATA = (0x8004C021, "No XML CDATA found")
    DRM_E_DSTNAMESPACEFULL = (0x8004C022, "No more room for DST Namespace")
    DRM_E_DST_NAMESPACE_NOT_FOUND = (0x8004C023, "No DST Namespace found")
    DRM_E_DST_SLOT_NOT_FOUND = (0x8004C024, "DST Dataslot not found")
    DRM_E_DST_SLOT_EXISTS = (0x8004C025, "DST Dataslot already exists")
    DRM_E_DST_CORRUPTED = (0x8004C026, "The data store is corrupted")
    DRM_E_DST_SEEK_ERROR = (0x8004C027, "There was an error attempting to seek in the Data Store")
    DRM_E_DSTNAMESPACEINUSE = (0x8004C028, "No DST Namespace in use")
    DRM_E_INVALID_SECURESTORE_PASSWORD = (0x8004C029, "The password used to open the secure store key was not able to validate the secure store hash.")
    DRM_E_SECURESTORE_CORRUPT = (0x8004C02A, "The secure store is corrupt")
    DRM_E_SECURESTORE_FULL = (0x8004C02B, "The current secure store key is full. No more data can be added.")
    DRM_E_NOACTIONINLICENSEREQUEST = (0x8004C02C, "No action(s) added for license request")
    DRM_E_DUPLICATED_HEADER_ATTRIBUTE = (0x8004C02D, "Duplicated attribute in Header")
    DRM_E_NO_KID_IN_HEADER = (0x8004C02E, "No KID attribute in Header")
    DRM_E_NO_LAINFO_IN_HEADER = (0x8004C02F, "No LAINFO attribute in Header")
    DRM_E_NO_CHECKSUM_IN_HEADER = (0x8004C030, "No Checksum attribute in Header")
    DRM_E_DST_BLOCK_MISMATCH = (0x8004C031, "DST block mismatch")
    DRM_E_BACKUP_EXISTS = (0x8004C032, "Backup file already exist.")
    DRM_E_LICENSE_TOOLONG = (0x8004C033, "License size is too long")
    DRM_E_DST_EXISTS = (0x8004C034, "A DST already exists in the specified location")
    DRM_E_INVALID_DEVICE_CERTIFICATE = (0x8004C035, "The device certificate is invalid.")
    DRM_E_DST_LOCK_FAILED = (0x8004C036, "Locking a segment of the DST failed.")
    DRM_E_FILE_SEEK_ERROR = (0x8004C037, "File Seek Error")
    DRM_E_DST_NOT_LOCKED_EXCLUSIVE = (0x8004C038, "Existing lock is not exclusive")
    DRM_E_DST_EXCLUSIVE_LOCK_ONLY = (0x8004C039, "Only exclusive lock is accepted")
    DRM_E_DSTRESERVEDKEYDETECTED = (0x8004C03A, "DST reserved key value detected in UniqueKey")
    DRM_E_V1_NOT_SUPPORTED = (0x8004C03B, "V1 Lic Acquisition is not supported")
    DRM_E_HEADER_NOT_SET = (0x8004C03C, "Content header is not set")
    DRM_E_NEEDDEVCERTINDIV = (0x8004C03D, "The device certificate is template. It need Devcert Indiv")
    DRM_E_MACHINE_ID_MISMATCH = (0x8004C03E, "The device has Machine Id different from that in devcert.")
    DRM_E_CLK_INVALID_RESPONSE = (0x8004C03F, "The secure clock response is invalid.")
    DRM_E_CLK_INVALID_DATE = (0x8004C040, "The secure clock response is invalid.")
    DRM_E_CLK_UNSUPPORTED_VALUE = (0x8004C041, "The secure clock response has unsupported value.")
    DRM_E_INVALIDDEVICECERTIFICATETEMPLATE = (0x8004C042, "The device certificate is invalid.")
    DRM_E_DEVCERT_EXCEEDS_SIZE_LIMIT = (0x8004C043, "The device certificate exceeds max size")
    DRM_E_DEVCERTTEMPLATEEXCEEDSSIZELIMIT = (0x8004C044, "The device certificate template exceeds max size")
    DRM_E_DEVCERTREADERROR = (0x8004C045, "Can't get the device certificate")
    DRM_E_DEVCERTWRITEERROR = (0x8004C046, "Can't store the device certificate")
    DRM_E_PRIVKEY_READ_ERROR = (0x8004C047, "Can't get device private key")
    DRM_E_PRIVKEYWRITEERROR = (0x8004C048, "Can't store device private key")
    DRM_E_DEVCERT_TEMPLATE_READ_ERROR = (0x8004C049, "Can't get the device certificate template")
    DRM_E_CLK_NOT_SUPPORTED = (0x8004C04A, "The secure clock is not supported.")
    DRM_E_DEVCERTINDIV_NOT_SUPPORTED = (0x8004C04B, "The Devcert Indiv is not supported.")
    DRM_E_METERING_NOT_SUPPORTED = (0x8004C04C, "The Metering is not supported.")
    DRM_E_CLK_RESETSTATEREADERROR = (0x8004C04D, "Can not read Secure clock Reset State.")
    DRM_E_CLK_RESETSTATEWRITEERROR = (0x8004C04E, "Can not write Secure clock Reset State.")
    DRM_E_XMLNOTFOUND = (0x8004C04F, "a required XML tag was not found")
    DRM_E_METERING_WRONG_TID = (0x8004C050, "wrong TID sent on metering response")
    DRM_E_METERING_INVALID_COMMAND = (0x8004C051, "wrong command sent on metering response")
    DRM_E_METERING_STORE_CORRUPT = (0x8004C052, "The metering store is corrupt")
    DRM_E_CERTIFICATE_REVOKED = (0x8004C053, "A certificate given to DRM was revoked.")
    DRM_E_CRYPTO_FAILED = (0x8004C054, "A cryptographic operation failed.")
    DRM_E_STACK_CORRUPT = (0x8004C055, "The stack allocator context is corrupt. Likely a buffer overrun problem.")
    DRM_E_UNKNOWN_BINDING_KEY = (0x8004C056, "A matching binding key could not be found for the license.")
    DRM_E_V1_LICENSE_CHAIN_NOT_SUPPORTED = (0x8004C057, "License chaining with V1 content is not supported.")
    DRM_E_WRONG_TOKEN_TYPE = (0x8004C058, "The wrong type of token was used.")
    DRM_E_POLICY_METERING_DISABLED = (0x8004C059, "Metering code was called but metering is disabled by group or user policy")
    DRM_E_POLICY_ONLINE_DISABLED = (0x8004C05A, "online communication is disabled by group policy")
    DRM_E_CLK_NOT_SET = (0x8004C05B, "Time based licenses can not be used because the secure clock is not set on the device.")
    DRM_E_NO_CLK_SUPPORTED = (0x8004C05C, "Time based licenses can not be used because the device does not support any clock.")
    DRM_E_NO_URL = (0x8004C05D, "Can not find URL info.")
    DRM_E_UNKNOWN_DEVICE_PROPERTY = (0x8004C05E, "Unknown device property.")
    DRM_E_METERING_MID_MISMATCH = (0x8004C05F, "The metering ID is not same in Metering Cert and metering response data")
    DRM_E_METERING_RESPONSE_DECRYPT_FAILED = (0x8004C060, "The encrypted section of metering response can not be decrypted")
    DRM_E_RIV_TOO_SMALL = (0x8004C063, "RIV on the machine is too small.")
    DRM_E_STACK_ALREADY_INITIALIZED = (0x8004C064, "DRM_STK_Init called for initialized stack")
    DRM_E_DEVCERT_REVOKED = (0x8004C065, "The device certificate given to DRM is revoked.")
    DRM_E_OEM_RSA_DECRYPTION_ERROR = (0x8004C066, "Error in OEM RSA Decryption.")
    DRM_E_INVALID_DEVSTORE_ATTRIBUTE = (0x8004C067, "Invalid device attributes in the device store")
    DRM_E_INVALID_DEVSTORE_ENTRY = (0x8004C068, "The device store data entry is corrupted")
    DRM_E_OEM_RSA_ENCRYPTION_ERROR = (0x8004C069, "Error in OEM RSA Encryption process")
    DRM_E_DST_NAMESPACE_EXISTS = (0x8004C06A, "The DST Namespace already exists.")
    DRM_E_PERF_SCOPING_ERROR = (0x8004C06B, "Error in performance scope context")
    DRM_E_PRECISION_ARITHMETIC_FAIL = (0x8004C06C, "Operation involving multiple precision arithmetic fails")
    DRM_E_OEM_RSA_INVALID_PRIVATE_KEY = (0x8004C06D, "Invalid private key.")
    DRM_E_NO_OPL_CALLBACK = (0x8004C06E, "There is no callback function to process the output restrictions specified in the license")
    DRM_E_INVALID_PLAYREADY_OBJECT = (0x8004C06F, "Structure of PlayReady object is invalid")
    DRM_E_DUPLICATE_LICENSE = (0x8004C070, "There is already a license in the store with the same KID & LID")
    DRM_E_REVOCATION_NOT_SUPPORTED = (0x8004C071, "Device does not support revocation, while revocation data was placed into license policy structure.")
    DRM_E_RECORD_NOT_FOUND = (0x8004C072, "Record with requested type was not found in PlayReady object.")
    DRM_E_BUFFER_BOUNDS_EXCEEDED = (0x8004C073, "An array is being referenced outside of it's bounds.")
    DRM_E_INVALID_BASE64 = (0x8004C074, "An input string contains invalid Base64 characters.")
    DRM_E_PROTOCOL_VERSION_NOT_SUPPORTED = (0x8004C075, "The protocol version is not supported.")
    DRM_E_INVALID_LICENSE_RESPONSE_SIGNATURE = (0x8004C076, "Cannot verify license acquisition's response because signature is invalid.")
    DRM_E_INVALID_LICENSE_RESPONSE_ID = (0x8004C077, "Cannot verify license acquisition's response because response ID is invalid.")
    DRM_E_LICENSE_RESPONSE_SIGNATURE_MISSING = (0x8004C078, "Cannot verify license acquisition's response because either response ID, license nonce or signature is missing.")
    DRM_E_INVALID_DOMAIN_JOIN_RESPONSE_SIGNATURE = (0x8004C079, "Cannot verify domain join response because signature is invalid.")
    DRM_E_DOMAIN_JOIN_RESPONSE_SIGNATURE_MISSING = (0x8004C07A, "Cannot verify domain join response because either signing certificate chain or signature is missing.")
    DRM_E_ACTIVATION_REQUIRED = (0x8004C07B, "The device must be activated before initialization can succeed.")
    DRM_E_ACTIVATION_INTERNAL_ERROR = (0x8004C07C, "A server error occurred during device activation.")
    DRM_E_ACTIVATION_GROUP_CERT_REVOKED_ERROR = (0x8004C07D, "The activation group cert has been revoked and the application must be updated with a new client lib.")
    DRM_E_ACTIVATION_NEW_CLIENT_LIB_REQUIRED_ERROR = (0x8004C07E, "The client lib used by the application is not supported and must be updated.")
    DRM_E_ACTIVATION_BAD_REQUEST = (0x8004C07F, "The activation request is invalid")
    DRM_E_FILEIO_ERROR = (0x8004C080, "Encountered a system error during file I/O.")
    DRM_E_DISKSPACE_ERROR = (0x8004C081, "Out of disk space for storing playready files.")
    DRM_E_UPLINK_LICENSE_NOT_FOUND = (0x8004C082, "A license was found in the license store but no license was found for its uplink ID.")
    DRM_E_ACTIVATION_CLIENT_ALREADY_CURRENT = (0x8004C083, "The activation client already has the lastest verion.")
    DRM_E_LICENSE_REALTIME_EXPIRED = (0x8004C084, "The license has expired during decryption due to the RealTimeExpiration Restriction.")
    DRM_E_DECRYPTOR_CANNOT_CLONE = (0x8004C085, "The decryptor cannot be cloned due to restrictions in the corresponding license.")
    DRM_E_ACTIVATION_REQUIRED_REACTIVATION_POSSIBLE = (0x8004C086, "The device must be activated or reactivated before initialization can succeed.")
    DRM_E_LRB_NOLGPUBKEY = (0x8004C0A0, "LRB does not contain a valid LGPUBKEY.")
    DRM_E_LRB_INVALIDSIGNATURE = (0x8004C0A1, "Signature inside LRB is invalid.")
    DRM_E_LRB_LGPUBKEY_MISMATCH = (0x8004C0A2, "LRB is signed with a pubkey different from LGPUBKEY")
    DRM_E_LRB_INVALIDLICENSEDATA = (0x8004C0A3, "LRB is signed with a pubkey different from LGPUBKEY")
    DRM_E_LICEVAL_LICENSE_NOT_SUPPLIED = (0x8004C0C0, "License not supplied in the liceval context")
    DRM_E_LICEVAL_KID_MISMATCH = (0x8004C0C1, "Mismatch between KID from header and the one inside license")
    DRM_E_LICEVAL_LICENSE_REVOKED = (0x8004C0C2, "License for this content has been revoked")
    DRM_E_LICEVAL_UPDATE_FAILURE = (0x8004C0C3, "Failed to update content revocation")
    DRM_E_LICEVAL_REQUIRED_REVOCATION_LIST_NOT_AVAILABLE = (0x8004C0C4, "Failed to update content revocation")
    DRM_E_LICEVAL_INVALID_PRND_LICENSE = (0x8004C0C5, "License is an invalid PRND license. PRND license cannot have metering ID, expire-after-first-play or domain properties.")
    DRM_E_XMR_OBJECT_ALREADY_EXISTS = (0x8004C0E0, "XMR builder context already has this object.")
    DRM_E_XMR_OBJECT_NOTFOUND = (0x8004C0E1, "XMR object was not found.")
    DRM_E_XMR_REQUIRED_OBJECT_MISSING = (0x8004C0E2, "XMR license doesn't have one or more required objects.")
    DRM_E_XMR_INVALID_UNKNOWN_OBJECT = (0x8004C0E3, "Invalid unknown object")
    DRM_E_XMR_LICENSE_BINDABLE = (0x8004C0E4, "XMR license does not contain the Cannot Bind right")
    DRM_E_XMR_LICENSE_NOT_BINDABLE = (0x8004C0E5, "XMR license cannot be bound to because of the Cannot Bind right")
    DRM_E_XMR_UNSUPPORTED_XMR_VERSION = (0x8004C0E6, "The version of XMR license is not supported for the current action")
    DRM_E_NOT_CRL_BLOB = (0x8004C100, "CRL blob provided for parsing does not start with CBLB. It means file is not CRL blob at all.")
    DRM_E_BAD_CRL_BLOB = (0x8004C101, "The file is structured as CRL blob, but there is some error in file structure or one of CRLs inside is invalid.")
    DRM_E_INVALID_DEVCERT_ATTRIBUTE = (0x8004C200, "The attributes in the Device certificate are invalid")
    DRM_E_TEST_PKCRYPTO_FAILURE = (0x8004C300, "Error in PK encryption/decryption crypto test cases.")
    DRM_E_TEST_PKSIGN_VERIFY_ERROR = (0x8004C301, "Digital signature verification failed.")
    DRM_E_TEST_ENCRYPT_ERROR = (0x8004C302, "Error in encryption of cipher text.")
    DRM_E_TEST_RC4KEY_FAILED = (0x8004C303, "RC4 key failed during crypto operations.")
    DRM_E_TEST_DECRYPT_ERROR = (0x8004C304, "Error in cipher text decryption.")
    DRM_E_TEST_DESKEY_FAILED = (0x8004C305, "Decrypted data not equal to original data in a DES operation.")
    DRM_E_TEST_CBC_INVERSEMAC_FAILURE = (0x8004C306, "Decrypted data not equal to original in Inverse MAC operation.")
    DRM_E_TEST_HMAC_FAILURE = (0x8004C307, "Error in hashed data in HMAC operation.")
    DRM_E_TEST_INVALIDARG = (0x8004C308, "Error in the number of arguments or argument data in Test files.")
    DRM_E_TEST_DEVICE_PRIVATE_KEY_INCORRECTLY_STORED = (0x8004C30A, "DRMManager context should not contain the device private key.")
    DRM_E_TEST_DRMMANAGER_CONTEXT_NULL = (0x8004C30B, "DRMManager context is NULL.")
    DRM_E_TEST_UNEXPECTED_REVINFO_RESULT = (0x8004C30C, "Revocation cache result was not as expected.")
    DRM_E_TEST_RIV_MISMATCH = (0x8004C30D, "Revocation Info Version(RIV) mismatch.")
    DRM_E_TEST_URL_ERROR = (0x8004C310, "There is an error in the URL from the challenge generated.")
    DRM_E_TEST_MID_MISMATCH = (0x8004C311, "The MIDs returned from the DRM_MANAGER_CONTEXT does not match the test input.")
    DRM_E_TEST_METER_CERTIFICATE_MISMATCH = (0x8004C312, "The input data does not match with the Metering certificate returned from the license.")
    DRM_E_TEST_LICENSE_STATE_MISMATCH = (0x8004C313, "The input data and license state returned from the license do not match.")
    DRM_E_TEST_SOURCE_ID_MISMATCH = (0x8004C316, "The input data and license state returned from the license do not match.")
    DRM_E_TEST_UNEXPECTED_LICENSE_COUNT = (0x8004C317, "The input data and the number of license from the KID do not match.")
    DRM_E_TEST_UNEXPECTED_DEVICE_PROPERTY = (0x8004C318, "Unknown device property.")
    DRM_E_TEST_DRMMANAGER_MISALIGNED_BYTES = (0x8004C319, "Error due to misalignment of bytes.")
    DRM_E_TEST_LICENSE_RESPONSE_ERROR = (0x8004C31A, "The license response callbacks did not provide the expected data.")
    DRM_E_TEST_OPL_MISMATCH = (0x8004C31B, "The minimum levels of the compressed/uncompressed Digital and Analog Video do not match the OPL.")
    DRM_E_TEST_INVALID_OPL_CALLBACK = (0x8004C31C, "The callback type supplied is not valid.")
    DRM_E_TEST_INCOMPLETE = (0x8004C31D, "The test function failed to complete.")
    DRM_E_TEST_UNEXPECTED_OUTPUT = (0x8004C31E, "The output of the function being tested does not match the expected output.")
    DRM_E_TEST_DLA_NO_CONTENT_HEADER = (0x8004C31F, "Content Header Information was not retrieved correctly in DLA Sync Tests.")
    DRM_E_TEST_DLA_CONTENT_HEADER_FOUND = (0x8004C320, "Content Header Information was found when it should not have been in DLA Sync Tests.")
    DRM_E_TEST_SYNC_LSD_INCORRECT = (0x8004C321, "DRM_SNC_GetSyncStoreEntry returned incorrect License State Data.")
    DRM_E_TEST_TOO_SLOW = (0x8004C322, "The performance test failed because DRM took longer than its maximum time.")
    DRM_E_TEST_LICENSESTORE_NOT_OPEN = (0x8004C323, "The License Store contexts in the App Manager context are not open.")
    DRM_E_TEST_DEVICE_NOT_INITED = (0x8004C324, "The device instance has not been initialized prior to use.")
    DRM_E_TEST_VARIABLE_NOT_SET = (0x8004C325, "A global variable needed for test execution has not been set correctly.")
    DRM_E_TEST_NOMORE = (0x8004C326, "The same as DRM_E_NOMORE, only explicitly used in test code.")
    DRM_E_TEST_FILE_LOAD_ERROR = (0x8004C327, "There was an error loading a test data file.")
    DRM_E_TEST_LICENSE_ACQ_FAILED = (0x8004C328, "The attempt to acquire a license failed.")
    DRM_E_TEST_UNSUPPORTED_FILE_FORMAT = (0x8004C329, "A file format is being used which is not supported by the test function.")
    DRM_E_TEST_PARSING_ERROR = (0x8004C32A, "There was an error parsing input parameter.")
    DRM_E_TEST_NOTIMPL = (0x8004C32B, "The specified test API is not implemented.")
    DRM_E_TEST_VARIABLE_NOTFOUND = (0x8004C32C, "The specified test varaible was not found in the shared variable table.")
    DRM_E_TEST_VARIABLE_LISTFULL = (0x8004C32D, "The shared test variable table is full.")
    DRM_E_TEST_UNEXPECTED_CONTENT_PROPERTY = (0x8004C32E, "Unknown content property.")
    DRM_E_TEST_PRO_HEADER_NOT_SET = (0x8004C32F, "PlayReady Object Header not set.")
    DRM_E_TEST_NON_PRO_HEADER_TYPE = (0x8004C330, "Incompatible header - PlayReady Object Header expected.")
    DRM_E_TEST_INVALID_DEVICE_WRAPPER = (0x8004C331, "The Device Simulator Device Wrapper is not valid.")
    DRM_E_TEST_INVALID_WMDM_WRAPPER = (0x8004C332, "The Device Simulator WMDM Wrapper is not valid.")
    DRM_E_TEST_INVALID_WPD_WRAPPER = (0x8004C333, "The Device Simulator WPD Wrapper is not valid.")
    DRM_E_TEST_INVALID_FILE = (0x8004C334, "The data file given was invalid.")
    DRM_E_TEST_PROPERTY_NOT_FOUND = (0x8004C335, "The object did not have the property which was queried.")
    DRM_E_TEST_METERING_DATA_INCORRECT = (0x8004C336, "The metering data reported is incorrect.")
    DRM_E_TEST_FILE_ALREADY_OPEN = (0x8004C337, "The handle variable for a test file is not NULL. This indicates that a file was opened and not closed properly.")
    DRM_E_TEST_FILE_NOT_OPEN = (0x8004C338, "The handle variable for a test file is NULL. This indicates that a file was not opened.")
    DRM_E_TEST_PICT_COLUMN_TOO_WIDE = (0x8004C339, "The PICT input file contains a column which is too wide for the test parser to handle.")
    DRM_E_TEST_PICT_COLUMN_MISMATCH = (0x8004C33A, "The PICT input file contains a row which doesn't have the same number of columns as the header row.")
    DRM_E_TEST_TUX_TEST_SKIPPED = (0x8004C33B, "TUX cannot find the speficied test case in target dll. Test Skipped.")
    DRM_E_TEST_KEYFILE_VERIFICATION_FAILURE = (0x8004C33C, "Verification of the Keyfile context failed.")
    DRM_E_TEST_DATA_VERIFICATION_FAILURE = (0x8004C33D, "Data does not match expected value and failed verification.")
    DRM_E_TEST_NET_FAIL = (0x8004C33E, "The Test failed to perform Network I/O.")
    DRM_E_TEST_CLEANUP_FAIL = (0x8004C33F, "A failure occurred during the test case cleanup phase.")
    DRM_E_TEST_LICGEN_UNSUPPORTED_VALUE = (0x8004C340, "A property used during license generation is not supported.")
    DRM_E_LOGICERR = (0x8004C3E8, "DRM code has a logic error in it.  This result should never be returned.  There is an unhandled code path if it is returned.")
    DRM_E_INVALID_REV_INFO = (0x8004C3E9, "The rev info blob is invalid.")
    DRM_E_SYNCLISTNOTSUPPORTED = (0x8004C3EA, "The device does not support synclist.")
    DRM_E_REVOCATION_BUFFER_TOO_SMALL = (0x8004C3EB, "The revocation buffer is too small.")
    DRM_E_DEVICE_ALREADY_REGISTERED = (0x8004C3EC, "There exists already a device in the device store with the same DEVICEID that was given.")
    DRM_E_DST_NOT_COMPATIBLE = (0x8004C3ED, "The data store version is incompatible with this version of DRM.")
    DRM_E_RSA_DECRYPTION_ERROR = (0x8004C3F0, "The data block/Encoded message used in OAEP decoding is incorrect.")
    DRM_E_OEM_RSA_MESSAGE_TOO_BIG = (0x8004C3F1, "The base message buffer is larger than the given modulus.")
    DRM_E_METERCERT_NOT_FOUND = (0x8004C3F2, "The metering certificate was not found in the store.")
    DRM_E_MODULAR_ARITHMETIC_FAILURE = (0x8004C3F3, "A failure occurred in bignum modular arithmetic.")
    DRM_E_FEATURE_NOT_SUPPORTED = (0x8004C3F4, "The feature is not supported in this release.")
    DRM_E_REVOCATION_INVALID_PACKAGE = (0x8004C3F5, "The revocation package is invalid")
    DRM_E_HWID_ERROR = (0x8004C3F6, "Failed to get the hardware ID.")
    DRM_E_VAR_NOT_INITIALIZED = (0x8004C3F7, "Variable was not initialized.")
    DRM_E_DOMAIN_INVALID_GUID = (0x8004C500, "Not a correct GUID.")
    DRM_E_DOMAIN_INVALID_CUSTOM_DATA_TYPE = (0x8004C501, "Not a valid custom data type.")
    DRM_E_DOMAIN_STORE_ADD_DATA = (0x8004C502, "Failed to add data into the domain store.")
    DRM_E_DOMAIN_STORE_GET_DATA = (0x8004C503, "Failed to retrieve data from the domain store.")
    DRM_E_DOMAIN_STORE_DELETE_DATA = (0x8004C504, "Failed to delete data from the domain store.")
    DRM_E_DOMAIN_STORE_OPEN_STORE = (0x8004C505, "Failed to open the domain store.")
    DRM_E_DOMAIN_STORE_CLOSE_STORE = (0x8004C506, "Failed to close the domain store.")
    DRM_E_DOMAIN_BIND_LICENSE = (0x8004C507, "Failed to bind to the domain license.")
    DRM_E_DOMAIN_INVALID_CUSTOM_DATA = (0x8004C508, "Not a valid custom data.")
    DRM_E_DOMAIN_NOT_FOUND = (0x8004C509, "No domain information is found.")
    DRM_E_DOMAIN_INVALID_DOMKEYXMR_DATA = (0x8004C50A, "The domain join response contains invalid domain privkey XMR data.")
    DRM_E_DOMAIN_STORE_INVALID_KEY_RECORD = (0x8004C50B, "Invalid format of domain private key record read from the domain store.")
    DRM_E_DOMAIN_JOIN_TOO_MANY_KEYS = (0x8004C50C, "The server returned too many domain keys for the client to handle.")
    DRM_E_DEVICE_DOMAIN_JOIN_REQUIRED = (0x8004C580, "This error code communicates to the application that the device is not a member of a domain. The app can uses this error code in turn to decide whether it needs to join the domain or not")
    DRM_E_SERVER_INTERNAL_ERROR = (0x8004C600, "An internal server error occurred.")
    DRM_E_SERVER_INVALID_MESSAGE = (0x8004C601, "The message sent to the server was invalid.")
    DRM_E_SERVER_DEVICE_LIMIT_REACHED = (0x8004C602, "The device limit for the domain has been reached.")
    DRM_E_SERVER_INDIV_REQUIRED = (0x8004C603, "Individualization of the client is required.")
    DRM_E_SERVER_SERVICE_SPECIFIC = (0x8004C604, "An error specific to the service has occurred.")
    DRM_E_SERVER_DOMAIN_REQUIRED = (0x8004C605, "A Domain certificate is required.")
    DRM_E_SERVER_RENEW_DOMAIN = (0x8004C606, "The Domain certificate needs to be renewed.")
    DRM_E_SERVER_UNKNOWN_METERINGID = (0x8004C607, "The metering identifier is unknown.")
    DRM_E_SERVER_COMPUTER_LIMIT_REACHED = (0x8004C608, "The computer limit for the domain has been reached.")
    DRM_E_SERVER_PROTOCOL_FALLBACK = (0x8004C609, "The client should fallback to the V2 license acquisition protocol.")
    DRM_E_SERVER_NOT_A_MEMBER = (0x8004C60A, "The client was removed from the domain in an offline fashion and thus still has a domain cert, but not a valid domain membership.")
    DRM_E_SERVER_PROTOCOL_VERSION_MISMATCH = (0x8004C60B, "The protocol version specified was not supported by the server.")
    DRM_E_SERVER_UNKNOWN_ACCOUNTID = (0x8004C60C, "The account identifier is unknown.")
    DRM_E_SERVER_PROTOCOL_REDIRECT = (0x8004C60D, "The protocol has a redirect.")
    DRM_E_SERVER_UNKNOWN_TRANSACTIONID = (0x8004C610, "The transaction identifier is unknown.")
    DRM_E_SERVER_INVALID_LICENSEID = (0x8004C611, "The license identifier is invalid.")
    DRM_E_SERVER_MAXIMUM_LICENSEID_EXCEEDED = (0x8004C612, "The maximum number of license identifiers in the request was exceeded.")
    DRM_E_LICACQ_TOO_MANY_LICENSES = (0x8004C700, "There are too many licenses in the license response.")
    DRM_E_LICACQ_ACK_TRANSACTION_ID_TOO_BIG = (0x8004C701, "The Transaction ID specified by the server exceeds the allocated buffer.")
    DRM_E_LICACQ_ACK_MESSAGE_NOT_CREATED = (0x8004C702, "The license acquisition acknowledgement message could not be created.")
    DRM_E_INITIATORS_UNKNOWN_TYPE = (0x8004C780, "The initiator type is unknown.")
    DRM_E_INITIATORS_INVALID_SERVICEID = (0x8004C781, "The service ID data is not valid.")
    DRM_E_INITIATORS_INVALID_ACCOUNTID = (0x8004C782, "The account ID data is not valid.")
    DRM_E_INITIATORS_INVALID_MID = (0x8004C783, "The account ID data is not valid.")
    DRM_E_INITIATORS_MISSING_DC_URL = (0x8004C784, "Domain Controller URL is missing.")
    DRM_E_INITIATORS_MISSING_CONTENT_HEADER = (0x8004C785, "Content header is missing.")
    DRM_E_INITIATORS_MISSING_LAURL_IN_CONTENT_HEADER = (0x8004C786, "Missing license acquisition URL in content header.")
    DRM_E_INITIATORS_MISSING_METERCERT_URL = (0x8004C787, "Meter certificate server URL is missing.")
    DRM_E_BCERT_INVALID_SIGNATURE_TYPE = (0x8004C800, "An invalid signature type was encountered")
    DRM_E_BCERT_CHAIN_TOO_DEEP = (0x8004C801, "There are, or there would be, too many certificates in the certificate chain")
    DRM_E_BCERT_INVALID_CERT_TYPE = (0x8004C802, "An invalid certificate type was encountered")
    DRM_E_BCERT_INVALID_FEATURE = (0x8004C803, "An invalid feature entry was encountered OR the porting kit was linked with mutually incompatible features or features incompatible with the certificate")
    DRM_E_BCERT_INVALID_KEY_USAGE = (0x8004C804, "An invalid public key usage was encountered")
    DRM_E_BCERT_INVALID_SECURITY_VERSION = (0x8004C805, "An invalid Indiv Box security version was encountered")
    DRM_E_BCERT_INVALID_KEY_TYPE = (0x8004C806, "An invalid public key type was encountered")
    DRM_E_BCERT_INVALID_KEY_LENGTH = (0x8004C807, "An invalid public key length was encountered")
    DRM_E_BCERT_INVALID_MAX_LICENSE_SIZE = (0x8004C808, "An invalid maximum license size value was encountered")
    DRM_E_BCERT_INVALID_MAX_HEADER_SIZE = (0x8004C809, "An invalid maximum license header size value was encountered")
    DRM_E_BCERT_INVALID_MAX_LICENSE_CHAIN_DEPTH = (0x8004C80A, "An invalid maximum license chain depth was encountered")
    DRM_E_BCERT_INVALID_SECURITY_LEVEL = (0x8004C80B, "An invalid security level was encountered")
    DRM_E_BCERT_PRIVATE_KEY_NOT_SPECIFIED = (0x8004C80C, "A private key for signing the certificate was not provided to the builder")
    DRM_E_BCERT_ISSUER_KEY_NOT_SPECIFIED = (0x8004C80D, "An issuer key was not provided to the builder")
    DRM_E_BCERT_ACCOUNT_ID_NOT_SPECIFIED = (0x8004C80E, "An account ID was not provided to the builder")
    DRM_E_BCERT_SERVICE_ID_NOT_SPECIFIED = (0x8004C80F, "A service provider ID was not provided to the builder")
    DRM_E_BCERT_CLIENT_ID_NOT_SPECIFIED = (0x8004C810, "A client ID was not provided to the builder")
    DRM_E_BCERT_DOMAIN_URL_NOT_SPECIFIED = (0x8004C811, "A domain URL was not provided to the builder")
    DRM_E_BCERT_DOMAIN_URL_TOO_LONG = (0x8004C812, "The domain URL contains too many ASCII characters")
    DRM_E_BCERT_HARDWARE_ID_NOT_SPECIFIED = (0x8004C813, "A hardware ID was not provided to the builder")
    DRM_E_BCERT_HARDWARE_ID_TOO_LONG = (0x8004C814, "A hardware ID is longer than the maximum supported bytes")
    DRM_E_BCERT_SERIAL_NUM_NOT_SPECIFIED = (0x8004C815, "A device serial number was not provided to the builder")
    DRM_E_BCERT_CERT_ID_NOT_SPECIFIED = (0x8004C816, "A certificate ID was not provided to the builder")
    DRM_E_BCERT_PUBLIC_KEY_NOT_SPECIFIED = (0x8004C817, "A public key for the certificate was not provided to the builder or not found by the parser")
    DRM_E_BCERT_KEY_USAGES_NOT_SPECIFIED = (0x8004C818, "The public key usage information was not provided to the builder or not found by the parser")
    DRM_E_BCERT_STRING_NOT_NULL_TERMINATED = (0x8004C819, "Data string is not null-teminated")
    DRM_E_BCERT_OBJECTHEADER_LEN_TOO_BIG = (0x8004C81A, "Object length in object header is too big")
    DRM_E_BCERT_INVALID_ISSUERKEY_LENGTH = (0x8004C81B, "IssuerKey Length value is invalid")
    DRM_E_BCERT_BASICINFO_CERT_EXPIRED = (0x8004C81C, "Certificate is expired")
    DRM_E_BCERT_UNEXPECTED_OBJECT_HEADER = (0x8004C81D, "Object header has unexpected values")
    DRM_E_BCERT_ISSUERKEY_KEYINFO_MISMATCH = (0x8004C81E, "The cert's Issuer Key does not match key info in the next cert")
    DRM_E_BCERT_INVALID_MAX_KEY_USAGES = (0x8004C81F, "Number of key usage entries is invalid")
    DRM_E_BCERT_INVALID_MAX_FEATURES = (0x8004C820, "Number of features is invalid")
    DRM_E_BCERT_INVALID_CHAIN_HEADER_TAG = (0x8004C821, "Cert chain header tag is invalid")
    DRM_E_BCERT_INVALID_CHAIN_VERSION = (0x8004C822, "Cert chain version is invalid")
    DRM_E_BCERT_INVALID_CHAIN_LENGTH = (0x8004C823, "Cert chain length value is invalid")
    DRM_E_BCERT_INVALID_CERT_HEADER_TAG = (0x8004C824, "Cert header tag is invalid")
    DRM_E_BCERT_INVALID_CERT_VERSION = (0x8004C825, "Cert version is invalid")
    DRM_E_BCERT_INVALID_CERT_LENGTH = (0x8004C826, "Cert length value is invalid")
    DRM_E_BCERT_INVALID_SIGNEDCERT_LENGTH = (0x8004C827, "Length of signed portion of certificate is invalid")
    DRM_E_BCERT_INVALID_PLATFORM_IDENTIFIER = (0x8004C828, "An invalid Platform Identifier was specified")
    DRM_E_BCERT_INVALID_NUMBER_EXTDATARECORDS = (0x8004C829, "An invalid number of extended data records")
    DRM_E_BCERT_INVALID_EXTDATARECORD = (0x8004C82A, "An invalid extended data record")
    DRM_E_BCERT_EXTDATA_LENGTH_MUST_PRESENT = (0x8004C82B, "Extended data record length must be present.")
    DRM_E_BCERT_EXTDATA_PRIVKEY_MUST_PRESENT = (0x8004C82C, "Extended data record length must be present.")
    DRM_E_BCERT_INVALID_EXTDATA_LENGTH = (0x8004C82D, "Calculated and written extended data object lengths do not match.")
    DRM_E_BCERT_EXTDATA_IS_NOT_PROVIDED = (0x8004C82E, "Extended data is not provided, the cert builder cannot write it.")
    DRM_E_BCERT_HWIDINFO_IS_MISSING = (0x8004C82F, "The PC certificate is correct but is not ready to use because has no HWID information")
    DRM_E_BCERT_INVALID_EXTDATA_SIGNED_LENGTH = (0x8004C830, "Length of signed portion of extended data info is invalid")
    DRM_E_BCERT_INVALID_EXTDATA_RECORD_TYPE = (0x8004C831, "Extended data record type is invalid")
    DRM_E_BCERT_EXTDATAFLAG_CERT_TYPE_MISMATCH = (0x8004C832, "Certificate of this type cannot have extended data flag set")
    DRM_E_BCERT_METERING_ID_NOT_SPECIFIED = (0x8004C833, "An metering ID was not provided to the builder")
    DRM_E_BCERT_METERING_URL_NOT_SPECIFIED = (0x8004C834, "A metering URL was not provided to the builder")
    DRM_E_BCERT_METERING_URL_TOO_LONG = (0x8004C835, "The metering URL contains too many ASCII characters")
    DRM_E_BCERT_VERIFICATION_ERRORS = (0x8004C836, "Verification errors are found while parsing cert chain")
    DRM_E_BCERT_REQUIRED_KEYUSAGE_MISSING = (0x8004C837, "Required key usage is missing")
    DRM_E_BCERT_NO_PUBKEY_WITH_REQUESTED_KEYUSAGE = (0x8004C838, "The certificate does not contain a public key with the requested key usage")
    DRM_E_BCERT_MANUFACTURER_STRING_TOO_LONG = (0x8004C839, "The manufacturer string is too long")
    DRM_E_BCERT_TOO_MANY_PUBLIC_KEYS = (0x8004C83A, "There are too many public keys in the certificate")
    DRM_E_BCERT_OBJECTHEADER_LEN_TOO_SMALL = (0x8004C83B, "Object length in object header is too small")
    DRM_E_BCERT_INVALID_WARNING_DAYS = (0x8004C83C, "An invalid server certificate expiration warning days. Warning days must be greater than zero.")
    DRM_E_BCERT_INVALID_DIGEST = (0x8004C83D, "The certificate digest is invalid.")
    DRM_E_BCERT_MANUFACTURING_INFO_REQUIRED = (0x8004C83E, "This certificate type requires Manufacturer Name, Model Name, and Model Number to be set.")
    DRM_E_XMLSIG_ECDSA_VERIFY_FAILURE = (0x8004C900, "Error in ECDSA signature verification.")
    DRM_E_XMLSIG_SHA_VERIFY_FAILURE = (0x8004C901, "Error in SHA verification.")
    DRM_E_XMLSIG_FORMAT = (0x8004C902, "The format of XML signature or encryption segment is incorrect.")
    DRM_E_XMLSIG_PUBLIC_KEY_ID = (0x8004C903, "Invalud pre-shared public key ID.")
    DRM_E_XMLSIG_INVALID_KEY_FORMAT = (0x8004C904, "Invalid type of public/private key format.")
    DRM_E_XMLSIG_SHA_HASH_SIZE = (0x8004C905, "Size of hash is unexpected.")
    DRM_E_XMLSIG_ECDSA_SIGNATURE_SIZE = (0x8004C906, "Size of ECDSA signature is unexpected.")
    DRM_E_UTF_UNEXPECTED_END = (0x8004CA00, "Unexpected end of data in the middle of multibyte character.")
    DRM_E_UTF_INVALID_CODE = (0x8004CA01, "UTF character maps into a code with invalid value.")
    DRM_E_SOAPXML_INVALID_STATUS_CODE = (0x8004CB00, "Status code contained in the server error response is invalid.")
    DRM_E_SOAPXML_XML_FORMAT = (0x8004CB01, "Cannot parse out expected XML node.")
    DRM_E_SOAPXML_WRONG_MESSAGE_TYPE = (0x8004CB02, "The message type associated with the soap message is wrong.")
    DRM_E_SOAPXML_SIGNATURE_MISSING = (0x8004CB03, "The message did not have a signature and needed one")
    DRM_E_SOAPXML_PROTOCOL_NOT_SUPPORTED = (0x8004CB04, "The requested protocol is not supported by the DRM SOAP parser.")
    DRM_E_SOAPXML_DATA_NOT_FOUND = (0x8004CB05, "The requested data is not found in the response.")
    DRM_E_CRYPTO_PUBLIC_KEY_NOT_MATCH = (0x8004CC00, "The public key associated with an encrypted domain private from the server does not match any public key on the device.")
    DRM_E_UNABLE_TO_RESOLVE_LOCATION_TREE = (0x8004CC01, "Unable to derive the key.  May be due to blackout or no rights to the service, etc.")
    DRM_E_SECURE_TRACE_BAD_GLOBAL_DATA_POINTER = (0x8004CD00, "The secure trace global data pointer is NULL")
    DRM_E_SECURE_TRACE_INVALID_GLOBAL_DATA = (0x8004CD01, "The secure trace global data structure is invalid")
    DRM_E_SECURE_TRACE_FORMATTING_ERROR = (0x8004CD02, "An error occured in formatting the trace message")
    DRM_E_SECURE_TRACE_BAD_SCHEME_DATA_POINTER = (0x8004CD03, "A secure trace scheme data pointer is NULL")
    DRM_E_SECURE_TRACE_BAD_PER_THREAD_AES_DATA_POINTER = (0x8004CD04, "The secure trace per thread AES data pointer is NULL")
    DRM_E_SECURE_TRACE_BAD_PER_THREAD_AES_BUFFER_POINTER = (0x8004CD05, "A secure trace per thread AES buffer pointer is NULL")
    DRM_E_SECURE_TRACE_AES_INSUFFICIENT_BUFFER = (0x8004CD06, "There is no space left in the secure trace AES buffer")
    DRM_E_SECURE_TRACE_VERSION_MISMATCH = (0x8004CD07, "All drm dlls do not agree on the same secure trace version")
    DRM_E_SECURE_TRACE_UNEXPECTED_ERROR = (0x8004CD08, "An expected error was encountered in secure tracing system")
    DRM_E_TEE_INVALID_KEY_DATA = (0x8004CD10, "The key data given to the TEE was invalid.")
    DRM_E_TEE_PROVISIONING_REQUIRED = (0x8004CD11, "Provisioning is required.")
    DRM_E_TEE_INVALID_HWDRM_STATE = (0x8004CD12, "The HWDRM state is invalid, e.g. the TEE context is invalid.  Reinitialization is required.")
    DRM_E_TEE_PROVISIONING_REQUEST_EXPIRED = (0x8004CD13, "Provisioning request expired.")
    DRM_E_TEE_CLOCK_NOT_SET = (0x8004CD14, "The TEE secure clock needs to be reset.")
    DRM_E_TEE_BLOB_ACCESS_DENIED = (0x8004CD15, "The blob data is protected and cannot be transfered outside of the TEE.")
    DRM_E_TEE_PROVISIONING_BAD_NONCE = (0x8004CD16, "Malformed nonce")
    DRM_E_TEE_PROVISIONING_NONCE_MISMATCH = (0x8004CD17, "Nonce mismatch. Possibly another request has happened in parallel.")
    DRM_E_TEE_ROOT_KEY_CHANGED = (0x8004CD18, "The root-most TEE key has changed without maintaining key history.  All TEE-bound data is now invalid.")
    DRM_E_TEE_PROVISIONING_INVALID_RESPONSE = (0x8004CD19, "Invalid provisioning response.")
    DRM_E_TEE_PROXY_INVALID_SERIALIZATION_MESSAGE = (0x8004CD1A, "Invalid TEE proxy serialization message.")
    DRM_E_TEE_PROXY_INVALID_SERIALIZATION_TYPE = (0x8004CD1B, "Invalid TEE proxy serialization type.")
    DRM_E_TEE_LAYER_UNINITIALIZED = (0x8004CD1C, "TEE Layer is not initialized.")
    DRM_E_TEE_INVALID_HEADER_FOOTER_SIZE = (0x8004CD1D, "The OEM defined TEE message header/footer size was not a multiple of 8 bytes.")
    DRM_E_TEE_MESSAGE_TOO_LARGE = (0x8004CD1E, "TEE method invocation message is too large.")
    DRM_E_TEE_CLOCK_DRIFTED = (0x8004CD1F, "TEE clock drift detected.")
    DRM_E_TEE_PROXY_INVALID_BUFFER_ALIGNMENT = (0x8004CD20, "The TEE serialization buffer is incorrectly aligned.  It requires 8-byte alignment.")
    DRM_E_TEE_PROXY_INVALID_ALIGNMENT = (0x8004CD21, "The TEE serialization buffer has parameters that are not properly aligned.")
    DRM_E_TEE_OUTPUT_PROTECTION_REQUIREMENTS_NOT_MET = (0x8004CD22, "The TEE has detected that certain output requirements are not being satisfied. Most commonly HDCP is required but not enabled on all available outputs.")
    DRM_E_ND_MUST_REVALIDATE = (0x8004CE00, "The client must be revalidated before executing the intended operation.")
    DRM_E_ND_INVALID_MESSAGE = (0x8004CE01, "A received message is garbled.")
    DRM_E_ND_INVALID_MESSAGE_TYPE = (0x8004CE02, "A received message contains an invalid message type.")
    DRM_E_ND_INVALID_MESSAGE_VERSION = (0x8004CE03, "A received message contains an invalid message version.")
    DRM_E_ND_INVALID_SESSION = (0x8004CE04, "The requested session is invalid.")
    DRM_E_ND_MEDIA_SESSION_LIMIT_REACHED = (0x8004CE05, "A new session cannot be opened because the maximum number of sessions has already been opened.")
    DRM_E_ND_UNABLE_TO_VERIFY_PROXIMITY = (0x8004CE06, "The proximity detection procedure could not confirm that the receiver is near the transmitter in the network.")
    DRM_E_ND_INVALID_PROXIMITY_RESPONSE = (0x8004CE07, "The response to the proximity detection challenge is invalid.")
    DRM_E_ND_DEVICE_LIMIT_REACHED = (0x8004CE08, "The maximum number of devices in use has been reached. Unable to open additional devices.")
    DRM_E_ND_BAD_REQUEST = (0x8004CE09, "The message format is invalid.")
    DRM_E_ND_FAILED_SEEK = (0x8004CE0A, "It is not possible to seek to the specified mark-in point.")
    DRM_E_ND_INVALID_CONTEXT = (0x8004CE0B, "Manager context or at least one of it's children is missing (or corrupt).")
    DRM_E_ASF_BAD_ASF_HEADER = (0x8004CF00, "The ASF file has a bad ASF header.")
    DRM_E_ASF_BAD_PACKET_HEADER = (0x8004CF01, "The ASF file has a bad packet header.")
    DRM_E_ASF_BAD_PAYLOAD_HEADER = (0x8004CF02, "The ASF file has a bad payload header.")
    DRM_E_ASF_BAD_DATA_HEADER = (0x8004CF03, "The ASF file has a bad data header.")
    DRM_E_ASF_INVALID_OPERATION = (0x8004CF04, "The intended operation is invalid given the current processing state of the ASF file.")
    DRM_E_ASF_AES_PAYLOAD_FOUND = (0x8004CF05, "ND payload extension system found; the file may be encrypted with AES already.")
    DRM_E_ASF_EXTENDED_STREAM_PROPERTIES_OBJ_NOT_FOUND = (0x8004CF06, "Extended stream properties object is not found; the file may be in non-supported outdated format.")
    DRM_E_ASF_INVALID_DATA = (0x8004CF20, "The packet is overstuffed with data.")
    DRM_E_ASF_TOO_MANY_PAYLOADS = (0x8004CF21, "The number of payloads in the packet is greater than the maximum allowed.")
    DRM_E_ASF_BANDWIDTH_OVERRUN = (0x8004CF22, "An object is overflowing the leaky bucket.")
    DRM_E_ASF_INVALID_STREAM_NUMBER = (0x8004CF23, "The stream number is invalid; it is either zero, greater than the maximum value allowed, or has no associated data.")
    DRM_E_ASF_LATE_SAMPLE = (0x8004CF24, "A sample was encountered with a presentation time outside of the mux's send window.")
    DRM_E_ASF_NOT_ACCEPTING = (0x8004CF25, "The sample does not fit in the remaining payload space.")
    DRM_E_ASF_UNEXPECTED = (0x8004CF26, "An unexpected error occurred.")
    DRM_E_NONCE_STORE_TOKEN_NOT_FOUND = (0x8004D000, "The matching nonce store token is not found.")
    DRM_E_NONCE_STORE_OPEN_STORE = (0x8004D001, "Fail to open nonce store.")
    DRM_E_NONCE_STORE_CLOSE_STORE = (0x8004D002, "Fail to close nonce store.")
    DRM_E_NONCE_STORE_ADD_LICENSE = (0x8004D003, "There is already a license associated with the nonce store token.")
    DRM_E_LICGEN_POLICY_NOT_SUPPORTED = (0x8004D100, "The license generation policy combination is not supported.")
    DRM_E_POLICYSTATE_NOT_FOUND = (0x8004D200, "The policy state is not found in the secure store.")
    DRM_E_POLICYSTATE_CORRUPTED = (0x8004D201, "The policy state is not stored as a valid internal format in the secure store.")
    DRM_E_MOVE_DENIED = (0x8004D300, "The requested move operation was denied by the service.")
    DRM_E_INVALID_MOVE_RESPONSE = (0x8004D301, "The move response was incorrectly formed.")
    DRM_E_MOVE_NONCE_MISMATCH = (0x8004D302, "The nonce in the repsonse did not match the expected value.")
    DRM_E_MOVE_TXID_MISMATCH = (0x8004D303, "The transaction id in the repsonse did not match the expected value.")
    DRM_E_MOVE_STORE_OPEN_STORE = (0x8004D304, "Failed to open the move store.")
    DRM_E_MOVE_STORE_CLOSE_STORE = (0x8004D305, "Failed to close the move store.")
    DRM_E_MOVE_STORE_ADD_DATA = (0x8004D306, "Failed to add data into the move store.")
    DRM_E_MOVE_STORE_GET_DATA = (0x8004D307, "Failed to retrieve data from the move store.")
    DRM_E_MOVE_FORMAT_INVALID = (0x8004D308, "The format of a move page or index is invalid.")
    DRM_E_MOVE_SIGNATURE_INVALID = (0x8004D309, "The signature of a move index is invalid.")
    DRM_E_COPY_DENIED = (0x8004D30A, "The requested copy operation was denied by the service.")
    DRM_E_XB_OBJECT_NOTFOUND = (0x8004D400, "The extensible binary object was not found.")
    DRM_E_XB_INVALID_OBJECT = (0x8004D401, "The extensible binary object format was invalid.")
    DRM_E_XB_OBJECT_ALREADY_EXISTS = (0x8004D402, "A single instance extensible binary object was encountered more than once.")
    DRM_E_XB_REQUIRED_OBJECT_MISSING = (0x8004D403, "A required extensible binary object was not found during building.")
    DRM_E_XB_UNKNOWN_ELEMENT_TYPE = (0x8004D404, "An extensible binary object description contained an element of an unknown type.")
    DRM_E_XB_INVALID_VERSION = (0x8004D405, "The serialized object version could not be found in the extensible binary object description.")
    DRM_E_XB_MAX_UNKNOWN_CONTAINER_DEPTH = (0x8004D406, "The maximum unknown container depth was reached.")
    DRM_E_XB_INVALID_ALIGNMENT = (0x8004D407, "The serialized message buffer is not properly aligned according to the XBinary format description.")
    DRM_E_XB_OBJECT_OUT_OF_RANGE = (0x8004D408, "An extensible binary object size or count is out of the range specified by the attributes 'MinSize' and 'MaxSize'.")
    DRM_E_KEYFILE_INVALID_PLATFORM = (0x8004D500, "The keyfile does not support the current platform.")
    DRM_E_KEYFILE_TOO_LARGE = (0x8004D501, "The keyfile is larger than the maximum supported size.")
    DRM_E_KEYFILE_PRIVATE_KEY_NOT_FOUND = (0x8004D502, "The private key requested was not found in the keyfile.")
    DRM_E_KEYFILE_CERTIFICATE_CHAIN_NOT_FOUND = (0x8004D503, "The certificate chain requested was not found in the keyfile.")
    DRM_E_KEYFILE_KEY_NOT_FOUND = (0x8004D504, "The AES Key ID was not found in the keyfile.")
    DRM_E_KEYFILE_UNKNOWN_DECRYPTION_METHOD = (0x8004D505, "Unknown keyfile decryption method.")
    DRM_E_KEYFILE_INVALID_SIGNATURE = (0x8004D506, "The keyfile signature was not valid.")
    DRM_E_KEYFILE_INTERNAL_DECRYPTION_BUFFER_TOO_SMALL = (0x8004D507, "The internal decryption buffer is too small to hold the encrypted key from the keyfile.")
    DRM_E_KEYFILE_PLATFORMID_MISMATCH = (0x8004D508, "Platform ID in the certificate does not match expected value.")
    DRM_E_KEYFILE_CERTIFICATE_ISSUER_KEY_MISMATCH = (0x8004D509, "Issuer key of the device certificate does not match public key of the model certificate.")
    DRM_E_KEYFILE_ROBUSTNESSVERSION_MISMATCH = (0x8004D50A, "Robustness version in the certificate does not match expected value.")
    DRM_E_KEYFILE_FILE_NOT_CLOSED = (0x8004D50B, "The KeyFile Close function was not called before trying to unintialize the KeyFile context.")
    DRM_E_KEYFILE_NOT_INITED = (0x8004D50C, "The KeyFile Context was not initialized before trying to use it.")
    DRM_E_KEYFILE_FORMAT_INVALID = (0x8004D50D, "The format of the KeyFile was invalid.")
    DRM_E_KEYFILE_UPDATE_NOT_ALLOWED = (0x8004D50E, "The keyfile of the device is read only, and updates are not permitted.")
    DRM_E_EMPTY_LA_URL = (0x8004D50F, "<No message>")
    DRM_E_PRND_MESSAGE_VERSION_INVALID = (0x8004D700, "The PRND message version is not supported.")
    DRM_E_PRND_MESSAGE_WRONG_TYPE = (0x8004D701, "This method does not processs this PRND message type.")
    DRM_E_PRND_MESSAGE_INVALID = (0x8004D702, "The PRND message does not conform to the PRND spec and is therefore invalid.")
    DRM_E_PRND_SESSION_ID_INVALID = (0x8004D703, "The Transmitter is unable to process a renewal Registration Request Message using a different session.  Use the session matching the previous session ID.")
    DRM_E_PRND_PROXIMITY_DETECTION_REQUEST_CHANNEL_TYPE_UNSUPPORTED = (0x8004D704, "The PRND Registration Request Message indicated that it only supports Proximity Detection Channel Types that the Transmitter does not support.")
    DRM_E_PRND_PROXIMITY_DETECTION_RESPONSE_INVALID = (0x8004D705, "The PRND Proximity Detection Response Message was successfully parsed but the nonce is invalid.")
    DRM_E_PRND_PROXIMITY_DETECTION_RESPONSE_TIMEOUT = (0x8004D706, "The PRND Proximity Detection Response Message was successfully processed but did not arrive in time to verify that the Receiver is Near the Transmitter.")
    DRM_E_PRND_LICENSE_REQUEST_CID_CALLBACK_REQUIRED = (0x8004D707, "The PRND License Request Message used Content Identifier Type Custom.  A Content Identifier Callback to convert the value to a KID is required.")
    DRM_E_PRND_LICENSE_RESPONSE_CLMID_INVALID = (0x8004D708, "The PRND License Response Message had an invalid Current License Message ID.")
    DRM_E_PRND_CERTIFICATE_NOT_RECEIVER = (0x8004D709, "The PRND Registration Request Message did not include a PlayReady certificate that supports the RECEIVER feature.")
    DRM_E_PRND_CANNOT_RENEW_USING_NEW_SESSION = (0x8004D70A, "The Receiver is unable to generate a renewal Registration Request Message using a new session.  Use the existing session.")
    DRM_E_PRND_INVALID_CUSTOM_DATA_TYPE = (0x8004D70B, "The Custom Data type is invalid. The first four bytes of Custom Data Type ID cannot be 0x4d534654 ( MSFT in ascii ).")
    DRM_E_PRND_CLOCK_OUT_OF_SYNC = (0x8004D70C, "The clock on the Receiver is not synchronized with the clock on the Transmitter.  Synchronize the clocks.")
    DRM_E_PRND_CANNOT_REBIND_PRND_RECEIVED_LICENSE = (0x8004D70D, "The license cannot be rebound to the PRND Receiver because it was itself received from a PRND Transmitter.")
    DRM_E_PRND_CANNOT_REGISTER_USING_EXISTING_SESSION = (0x8004D70E, "The Receiver is unable to generate a non-renewal Registration Request Message using an existing session.  End the existing session first or use a new session.")
    DRM_E_PRND_BUSY_PERFORMING_RENEWAL = (0x8004D70F, "The Receiver is currently unable to process a message of this type because it is in the middle of renewing the session.")
    DRM_E_PRND_LICENSE_REQUEST_INVALID_ACTION = (0x8004D710, "Play with no qualifier during license request is all that's supported in v1 of the PRND protocol.")
    DRM_E_PRND_TRANSMITTER_UNAUTHORIZED = (0x8004D711, "The Transmitter attempted to authorize with the Receiver but was unsuccessful.")
    DRM_E_PRND_TX_SESSION_EXPIRED = (0x8004D712, "The Transmitter session is expired.")
    DRM_E_PRND_INCOMPLETE_PROXIMITY_DETECTION = (0x8004D713, "The proximity detection hasn't completed successfully.")
    DRM_E_PRND_INVALID_CERT_DIGEST = (0x8004D714, "The given certificate digest doesn't match the one stored in the MTKB")
    DRM_E_OEMHAL_NOT_INITIALIZED = (0x8004D780, "The OEM HAL is not initialized.")
    DRM_E_OEMHAL_OUT_OF_KEY_REGISTERS = (0x8004D781, "There are no more key registers available in the OEM HAL implementation.")
    DRM_E_OEMHAL_KEYS_IN_USE = (0x8004D782, "The OEM HAL is being shutdown whilst keys are still allocated.")
    DRM_E_OEMHAL_NO_KEY = (0x8004D783, "The requested preloaded key is not available or the key handle is otherwise invalid.")
    DRM_E_OEMHAL_UNSUPPORTED_KEY_TYPE = (0x8004D784, "The specified key type cannot be used for the operation requested.")
    DRM_E_OEMHAL_UNSUPPORTED_KEY_WRAPPING_FORMAT = (0x8004D785, "The specified wrapping key type cannot be used to unwrap the specified key.")
    DRM_E_OEMHAL_UNSUPPORTED_KEY_LENGTH = (0x8004D786, "The key buffer provided is of the wrong length for the specified key/wrapping key combination.")
    DRM_E_OEMHAL_UNSUPPORTED_HASH_TYPE = (0x8004D787, "The specified hash type is not supported.")
    DRM_E_OEMHAL_UNSUPPORTED_SIGNATURE_SCHEME = (0x8004D788, "The specified signature scheme is not supported.")
    DRM_E_OEMHAL_BUFFER_TOO_LARGE = (0x8004D789, "The output buffer is larger than the input buffer and must be the same size.")
    DRM_E_OEMHAL_SAMPLE_ENCRYPTION_MODE_NOT_PERMITTED = (0x8004D78A, "The sample encryption mode is not permitted for this combination of encrypt parameters.")
    DRM_E_M2TS_PAT_PID_IS_NOT_ZERO = (0x8004D800, "PID 0 is reserved for PAT and cannot be used for other type of packet.")
    DRM_E_M2TS_PTS_NOT_EXIST = (0x8004D801, "The audio/video PES doesn' have the PTS data.")
    DRM_E_M2TS_PES_PACKET_LENGTH_NOT_SPECIFIED = (0x8004D802, "The audio PES' packet length is 0 which is not allowed.")
    DRM_E_M2TS_OUTPUT_BUFFER_FULL = (0x8004D803, "The output buffer for receiving the encrypted packets is full.")
    DRM_E_M2TS_CONTEXT_NOT_INITIALIZED = (0x8004D804, "The encryptor context hasn't been initialized yet.")
    DRM_E_M2TS_NEED_KEY_DATA = (0x8004D805, "The key data for encrypting the sample is either hasn't been set or the encryptor needs next key due to key rotation.")
    DRM_E_M2TS_DDPLUS_FORMAT_INVALID = (0x8004D806, "Not supported DDPlus format.")
    DRM_E_M2TS_NOT_UNIT_START_PACKET = (0x8004D807, "The encryptor expects a unit start packet.  The unit start packet should appear before the rest of the packets in the unit.")
    DRM_E_M2TS_TOO_MANY_SUBSAMPLES = (0x8004D808, "Too many subsamples over the limit that the ECM allows.")
    DRM_E_M2TS_TABLE_ID_INVALID = (0x8004D809, "The PAT or PMT packet contains an invalid table ID.")
    DRM_E_M2TS_PACKET_SYNC_BYTE_INVALID = (0x8004D80A, "The TS packet doesn't start with the 0x47 (sync byte).")
    DRM_E_M2TS_ADAPTATION_LENGTH_INVALID = (0x8004D80B, "The adaptation field length is invalid.")
    DRM_E_M2TS_PAT_HEADER_INVALID = (0x8004D80C, "There is an error in PAT header, unable to parse it.")
    DRM_E_M2TS_PMT_HEADER_INVALID = (0x8004D80D, "There is an error in PMT header, unable to parse it.")
    DRM_E_M2TS_PES_START_CODE_NOT_FOUND = (0x8004D80E, "Cannot find the PES start code (0x000001).")
    DRM_E_M2TS_STREAM_OR_PACKET_TYPE_CHANGED = (0x8004D80F, "The stream type or packet type of an existing PID has changed")
    DRM_E_M2TS_INTERNAL_ERROR = (0x8004D810, "An internal error occurred during encryptrion.")
    DRM_E_M2TS_ADTS_FORMAT_INVALID = (0x8004D811, "Not supported ADTS format.")
    DRM_E_M2TS_MPEGA_FORMAT_INVALID = (0x8004D812, "Not supported MPEGA format.")
    DRM_E_M2TS_CA_DESCRIPTOR_LENGTH_INVALID = (0x8004D813, "The CA_descruptor length is greater than ES_info length.")
    DRM_E_M2TS_CRC_FIELD_INVALID = (0x8004D814, "The CRC field in the PAT or PMT packet is invalid.")
    DRM_E_M2TS_INCOMPLETE_SECTION_HEADER = (0x8004D815, "The section header of a PES is not completed while the next PES packet has started already")
    DRM_E_M2TS_INVALID_UNALIGNED_DATA = (0x8004D816, "Not allowed to have the overflow of the unaligned payload to accross more than one PES")
    DRM_E_M2TS_GET_ENCRYPTED_DATA_FIRST = (0x8004D817, "Do not pass additional data for encryption when the last encryption result is DRM_S_MORE_DATA")
    DRM_E_M2TS_CANNOT_CHANGE_PARAMETER = (0x8004D818, "Not allowed to change the encryption parameter once the encryption started, i.e. after Drm_M2ts_Encrypt is called")
    DRM_E_M2TS_UNKNOWN_PACKET = (0x8004D819, "This packet appears before the first PAT and/or PMT and will be dropped.")
    DRM_E_M2TS_DROP_PACKET = (0x8004D820, "This packet should be dropped because at least one field in the packet contains an invalid data.")
    DRM_E_M2TS_DROP_PES = (0x8004D821, "This PES packet should be dropped because the PES packet is not valid.")
    DRM_E_M2TS_INCOMPLETE_PES = (0x8004D822, "This PES packet has one or more missing packets.")
    DRM_E_M2TS_WAITED_TOO_LONG = (0x8004D823, "This packet is dropped because its unit is not completed after a long period of time.")
    DRM_E_M2TS_SECTION_LENGTH_INVALID = (0x8004D824, "The section length inside the PAT or PMT is less than the minimun PAT or PMT section.")
    DRM_E_M2TS_PROGRAM_INFO_LENGTH_INVALID = (0x8004D825, "The sum of the program info length and the other fields in the PMT section don't match with the section length.")
    DRM_E_M2TS_PES_HEADER_INVALID = (0x8004D826, "Failed to parse the PES header, the PES maybe too short.")
    DRM_E_M2TS_ECM_PAYLOAD_OVER_LIMIT = (0x8004D827, "The size of the ECM payload exceeds the limit of 64k bytes")
    DRM_E_M2TS_SET_CA_PID_FAILED = (0x8004D828, "Unable to assign a PID for CA_PID, all PIDs in the range of 0x0010 to 0x1FFE are used.")
    DRM_E_LICGEN_CANNOT_PERSIST_LICENSE = (0x8004D901, "A non-persistent license cannot be stored in the license store.")
    DRM_E_LICGEN_PERSISTENT_REMOTE_LICENSE = (0x8004D902, "A remote bound license should be non-persistent.")
    DRM_E_LICGEN_EXPIRE_AFTER_FIRST_PLAY_REMOTE_LICENSE = (0x8004D903, "A remote bound license should not have expire after first play property.")
    DRM_E_LICGEN_ROOT_LICENSE_CANNOT_ENCRYPT = (0x8004D904, "A root license should not be used to encrypt content.")
    DRM_E_LICGEN_EMBED_LOCAL_LICENSE = (0x8004D905, "A local bound license cannot be embedded.")
    DRM_E_LICGEN_LOCAL_LICENSE_WITH_REMOTE_CERTIFICATE = (0x8004D906, "A local bound license cannot be bound to a remote certificate.")
    DRM_E_LICGEN_PLAY_ENABLER_REMOTE_LICENSE = (0x8004D907, "A remote bound license cannot have play enablers other than Passing to Unknown Output or Passing Constrained Resolution to Unknown Output.")
    DRM_E_LICGEN_DUPLICATE_PLAY_ENABLER = (0x8004D908, "A license descriptor contains a duplicate play enabler.")
    DRM_E_LICGEN_CHILD_SECURITY_LEVEL_TOO_LOW = (0x8004D909, "The security level of the chained license is too low.")
    DRM_E_H264_PARSING_FAILED = (0x8004DA00, "The H264 was unable to be parsed.")
    DRM_E_H264_SPS_PROFILE = (0x8004DA01, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_IDC = (0x8004DA02, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_SPSID = (0x8004DA03, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_FRAMENUM = (0x8004DA04, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_POCTYPE = (0x8004DA05, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_POCLSB = (0x8004DA06, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_POCCYCLE = (0x8004DA07, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_NUMREFFRAMES = (0x8004DA08, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_CHROMATOP = (0x8004DA09, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_CHROMABOTTOM = (0x8004DA0A, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_NALHRD = (0x8004DA0B, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_VLDHRD = (0x8004DA0C, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_VUIBPPD = (0x8004DA0D, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_VUIBPMD = (0x8004DA0E, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_VUIMMLH = (0x8004DA0F, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_VUIMMLV = (0x8004DA10, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_VUINRF = (0x8004DA11, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_VUIMDFB = (0x8004DA12, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_WIDTH_HEIGHT = (0x8004DA13, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_AREA = (0x8004DA14, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_MINHEIGHT2 = (0x8004DA15, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_MINHEIGHT3 = (0x8004DA16, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_CROPWIDTH = (0x8004DA17, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_CROPHEIGHT = (0x8004DA18, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_MORE_RBSP = (0x8004DA19, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_CHROMA_IDC = (0x8004DA1A, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_BITDEPTHLUMA = (0x8004DA1B, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_BITDEPTHCHROMA = (0x8004DA1C, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_DELTASCALE1 = (0x8004DA1D, "SPS-specific H264 parsing error")
    DRM_E_H264_SPS_DELTASCALE2 = (0x8004DA1E, "SPS-specific H264 parsing error")
    DRM_E_H264_BITSTREAM_TOOMANY = (0x8004DA30, "Bitstream-specific H264 parsing error")
    DRM_E_H264_BITSTREAM_TOOSHORT1 = (0x8004DA31, "Bitstream-specific H264 parsing error")
    DRM_E_H264_BITSTREAM_TOOSHORT2 = (0x8004DA32, "Bitstream-specific H264 parsing error")
    DRM_E_H264_BITSTREAM_TOOSHORT3 = (0x8004DA33, "Bitstream-specific H264 parsing error")
    DRM_E_H264_BITSTREAM_TOOSHORT4 = (0x8004DA34, "Bitstream-specific H264 parsing error")
    DRM_E_H264_BITSTREAM_TOOSHORT5 = (0x8004DA35, "Bitstream-specific H264 parsing error")
    DRM_E_H264_BITSTREAM_EXGOLOBMTOOLONG1 = (0x8004DA36, "Bitstream-specific H264 parsing error")
    DRM_E_H264_BITSTREAM_EXGOLOBMTOOLONG2 = (0x8004DA37, "Bitstream-specific H264 parsing error")
    DRM_E_H264_NALU_NO_START_CODE = (0x8004DA40, "Nalu-specific H264 parsing error")
    DRM_E_H264_NALU_ALL_ZERO = (0x8004DA41, "Nalu-specific H264 parsing error")
    DRM_E_H264_NALU_EMULATION = (0x8004DA42, "Nalu-specific H264 parsing error")
    DRM_E_H264_PPS_PPSID = (0x8004DA50, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_SPSID = (0x8004DA51, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_SPS_NOT_FOUND = (0x8004DA52, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_NUM_SLICE_GROUPS = (0x8004DA53, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_SLICE_GROUP_MAX = (0x8004DA54, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_RUN_LENGTH = (0x8004DA55, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_TOP_LEFT = (0x8004DA56, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_SLICE_GROUP_RATE = (0x8004DA57, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_SLICE_GROUP_MAP = (0x8004DA58, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_SLICE_GROUP_ID = (0x8004DA59, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_REF_IDX_L0 = (0x8004DA5A, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_REF_IDX_L1 = (0x8004DA5B, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_WEIGHTED_BIPRED = (0x8004DA5C, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_PIC_INIT_QP = (0x8004DA5D, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_PIC_INIT_QS = (0x8004DA5E, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_PIC_CHROMA_QP = (0x8004DA5F, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_REDUN_PIC_COUNT = (0x8004DA61, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_DELTA_SCALE1 = (0x8004DA62, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_DELTA_SCALE2 = (0x8004DA63, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_SECOND_CHROMA_QP = (0x8004DA64, "PPS-specific H264 parsing error")
    DRM_E_H264_PPS_MORE_RBSP = (0x8004DA65, "PPS-specific H264 parsing error")
    DRM_E_H264_SH_SLICE_TYPE = (0x8004DA70, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_SLICE_TYPE_UNSUPPORTED = (0x8004DA71, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_PPSID = (0x8004DA72, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_PPS_NOT_FOUND = (0x8004DA73, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_SPS_NOT_FOUND = (0x8004DA74, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_SLICE_TYPE_PROFILE = (0x8004DA75, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_IDR_FRAME_NUM = (0x8004DA76, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_FIRST_MB_IN_SLICE = (0x8004DA77, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_IDR_PIC_ID = (0x8004DA78, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_REDUN_PIC_COUNT = (0x8004DA79, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_NUM_REF_IDX_LX0 = (0x8004DA7A, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_NUM_REF_IDX_LX1 = (0x8004DA7B, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_REF_PIC_LIST_REORDER0 = (0x8004DA7C, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_REF_PIC_LIST_REORDER1 = (0x8004DA7D, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_LUMA_WEIGHT_DENOM = (0x8004DA7E, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_CHROMA_WEIGHT_DENOM = (0x8004DA7F, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_WP_WEIGHT_LUMA0 = (0x8004DA80, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_WP_OFFSET_LUMA0 = (0x8004DA81, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_WP_WEIGHT_CHROMA0 = (0x8004DA82, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_WP_OFFSET_CHROMA0 = (0x8004DA83, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_WP_WEIGHT_LUMA1 = (0x8004DA84, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_WP_OFFSET_LUMA1 = (0x8004DA85, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_WP_WEIGHT_CHROMA1 = (0x8004DA86, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_WP_OFFSET_CHROMA1 = (0x8004DA87, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_NUM_REF_PIC_MARKING = (0x8004DA88, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_MMCO4_DUPLICATE = (0x8004DA89, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_MMCO4_MAX_LONG_TERM_FRAME = (0x8004DA8A, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_MMCO5_DUPLICATE = (0x8004DA8B, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_MMCO5_FOLLOWS_MMC06 = (0x8004DA8C, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_MMCO5_COEXIST_MMCO_1_OR_3 = (0x8004DA8D, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_MMCO6_DUPLICATE = (0x8004DA8E, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_MODEL_NUMBER = (0x8004DA8F, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_SLICE_QP = (0x8004DA90, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_LF_ALPHA_C0_OFFSET = (0x8004DA91, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_LF_BETA_OFFSET = (0x8004DA92, "Slice-Header-specific H264 parsing error")
    DRM_E_H264_SH_SLICE_GROUP_CHANGE = (0x8004DA93, "Slice-Header-specific H264 parsing error")
    DRM_E_RPROV_INVALID_REQUEST = (0x8004DB00, "Invalid Remote provisioning request received.")
    DRM_E_RPROV_VERSION_MISSMATCH = (0x8004DB01, "Invalid Remote provisioning version received.")
    DRM_E_RPROV_INVALID_RESPONSE = (0x8004DB02, "Invalid response received.")
    DRM_E_RPROV_BOOTSTRAP_FAILURE = (0x8004DB03, "Remote provisioning bootstrap failed.")
    DRM_E_FIRMWARE_REVOKED = (0x8004DB04, "TEE Firmware is revoked; firmware update necessary.")
    DRM_E_RPROV_SKIP_BOOTSTRAP = (0x8004DB05, "Remote provisioning does not need bootstrap.")
    DRM_E_SECURESTOP_STORE_CORRUPT = (0x8004DC00, "The secure stop store is corrupted.")
    DRM_E_SECURESTOP_SESSION_LOCKED = (0x8004DC02, "The secure stop session is locked and may not be modified.")
    DRM_E_SECURESTOP_SESSION_CORRUPT = (0x8004DC03, "The secure stop session data is corrupted.")
    DRM_E_SECURESTOP_SESSION_ACTIVE = (0x8004DC04, "The secure stop session is active and cannot be locked.")
    DRM_E_SECURESTOP_SESSION_NOT_FOUND = (0x8004DC05, "The secure stop session could not be found in the data store.")
    DRM_E_SECURESTOP_INVALID_RESPONSE = (0x8004DC06, "The secure stop response is invalid.")
    DRM_E_SECURESTOP_SESSION_STOPPED = (0x8004DC07, "The secure stop session is stopped and may not be used for decryption.")
    DRM_E_SECURESTOP_INVALID_PUBLISHER_ID = (0x8004DC08, "Trying to generate a challenge with a publisher ID that doesn't match the one associated with the session.")
    DRM_E_SECURESTOP_PUBLISHER_ID_INCONSISTENT = (0x8004DC09, "Licenses acquired within the same session don't have the same secure stop publisher ID.")
    DRM_E_SECURESTOP_INCONSISTENT = (0x8004DC0A, "Some licenses acquired within the same session have secure stop while others don't.")
    DRM_E_MUTEX_ACQUIRE_FAILED = (0x8004DD00, "The mutex acquire for critical section failed.")
    DRM_E_MUTEX_LEAVE_FAILED = (0x8004DD01, "The mutex leave for critical section failed.")
    DRM_E_OEM_DPU_IS_BUSY = (0x8004DD02, "The DPU is still busy handling the previous request.")
    DRM_E_OEM_DPU_TIMEOUT_FOR_HDCP_TYPE1_LOCK_REQUEST = (0x8004DD03, "The DPU can not finish the command handling from SEC2 before timeout.")
    DRM_E_OEM_HDCP_TYPE1_LOCK_FAILED = (0x8004DD04, "The DPU failed to lock HDCP2.2 type as requested by SEC2.")
    DRM_E_OEM_HDCP_TYPE1_LOCK_UNKNOWN = (0x8004DD05, "The HDCP type1 lock RESPONSE value set by DPU is unknown.")
    DRM_E_OEM_BAR0_PRIV_WRITE_ERROR = (0x8004DD06, "The register could not be written due to PRI failure.")
    DRM_E_OEM_BAR0_PRIV_READ_ERROR = (0x8004DD07, "The register could not be read due to PRI failure.")
    DRM_E_OEM_DMA_FAILURE = (0x8004DD08, "The DMA transaction failure.")
    DRM_E_OEM_UNSUPPORTED_HS_ACTION = (0x8004DD09, "The requested HS action is not supported.")
    DRM_E_OEM_UNSUPPORTED_KDF = (0x8004DD0A, "The KDF is not supported in OEM's encryption/decryption implementation.")
    DRM_E_OEM_INVALID_AES_CRYPTO_MODE = (0x8004DD0B, "The requested AES crypto mode is invalid.")
    DRM_E_OEM_HS_CHK_INVALID_INPUT = (0x8004DD0C, "One or more of the input arguments to HS mode are invalid.")
    DRM_E_OEM_HS_CHK_CHIP_NOT_SUPPORTED = (0x8004DD0D, "The GPU does not support playready.")
    DRM_E_OEM_HS_CHK_UCODE_REVOKED = (0x8004DD0E, "Current ucode was revoked.")
    DRM_E_OEM_HS_CHK_NOT_IN_LSMODE = (0x8004DD0F, "Relevant falcon (depending upon the context from which this error code is being returned) is not in LS mode.")
    DRM_E_OEM_HS_CHK_INVALID_LS_PRIV_LEVEL = (0x8004DD10, "Relevant falcon (depending upon the context from which this error code is being returned) is not at proper LS priv level.")
    DRM_E_OEM_HS_CHK_INVALID_REGIONCFG = (0x8004DD11, "The REGIONCFG is not set to correct WPR region.")
    DRM_E_OEM_HS_CHK_PRIV_SEC_DISABLED_ON_PROD = (0x8004DD12, "The priv sec is unexpectedly disabled on production board.")
    DRM_E_OEM_HS_CHK_SW_FUSING_ALLOWED_ON_PROD = (0x8004DD13, "The SW fusing is unexpectedly allowed on production board.")
    DRM_E_OEM_HS_CHK_INTERNAL_SKU_ON_PROD = (0x8004DD14, "The SKU is internal on production board.")
    DRM_E_OEM_HS_CHK_DEVID_OVERRIDE_ENABLED_ON_PROD = (0x8004DD15, "The devid override is enabled on production board.")
    DRM_E_OEM_HS_CHK_INCONSISTENT_PROD_MODES = (0x8004DD16, "The falcons in GPU are not in consistent debug/production mode.")
    DRM_E_OEM_HS_CHK_HUB_ENCRPTION_DISABLED = (0x8004DD17, "The hub encryption is not enabled on FB.")
    DRM_E_OEM_HS_PR_ILLEGAL_LASSAHS_STATE_AT_HS_ENTRY = (0x8004DD18, "LASSAHS is not in a correct state before doing HS entry")
    DRM_E_OEM_HS_PR_ILLEGAL_LASSAHS_STATE_AT_MPK_DECRYPT = (0x8004DD19, "LASSAHS is not in a correct state before doing MPK decryption")
    DRM_E_OEM_HS_PR_ILLEGAL_LASSAHS_STATE_AT_HS_EXIT = (0x8004DD1A, "LASSAHS is not in a correct state before doing HS exit")
    DRM_E_OEM_PREENTRY_GDK_OUT_OF_MEMORY = (0x8004DD1B, "Preallocation for GDK failed")
    DRM_E_OEM_GDK_IMEM_BLOCK_REVALIDATION_FAILED = (0x8004DD1C, "Failed to revalidate imem blocks invalidated during LASSAHS")
    DRM_E_OEM_INVALID_PDI = (0x8004DD1D, "The read PDI value is invalid")
    DRM_E_OEM_INVALID_SIZE_OF_CDKBDATA = (0x8004DD1E, "The size of NV_KB_CDKBData is not multiple of 16")
    DRM_E_SE_CRYPTO_MUTEX_ACQUIRE_FAILED = (0x8004DD1F, "Failed to acquire the Security Engine mutex for cypto operations")
    DRM_E_SE_CRYPTO_MUTEX_RELEASE_FAILED = (0x8004DD20, "Failed to release the Security Engine mutex for cypto operations")
    DRM_E_SE_CRYPTO_POINT_NOT_ON_CURVE = (0x8004DD21, "Point is not on the elliptic curve")
    DRM_E_OEM_WAIT_FOR_BAR0_IDLE_FAILED = (0x8004DD22, "WFI on a PRI read/write failed")
    DRM_E_OEM_ERROR_PRI_UNEXPECTED_FAILURE = (0x8004DD23, "DRM errors.")
    DRM_E_OEM_CSB_PRIV_WRITE_ERROR = (0x8004DD24, "The register could not be written due to CSB PRI failure.")
    DRM_E_OEM_CSB_PRIV_READ_ERROR = (0x8004DD25, "The register could not be read due to CSB PRI failure.")
    DRM_E_OEM_HS_MUTEX_ACQUIRE_FAILED = (0x8004DD26, "The mutex acquire for critical section at HS mode failed.")
    DRM_E_OEM_HS_MUTEX_RELEASE_FAILED = (0x8004DD27, "The mutex leave for critical section at HS mode failed.")
    DRM_E_MUTEX_INVALIDARG = (0x8004DDC1, "The Mutex ID is invalid.")
    DRM_E_MUTEX_ACQUIRE_GETTIME_FAILED = (0x8004DDC2, "Failed to get current time during mutex acquisition.")
    DRM_E_MUTEX_ACQUIRE_BAD_ID_VALUE = (0x8004DDC3, "The token ID obtained during mutex acquisition is invalid.")
    DRM_E_MUTEX_ACQUIRE_BAD_SHAREDATA = (0x8004DDC4, "Frame Buffer address of SEC-NVDEC shared structure is invalid.")
    DRM_E_MUTEX_ACQUIRE_TIMEOUT = (0x8004DDC5, "Timeout occured during mutex acquisition.")
    DRM_E_SECUREBUS_TIMEOUT = (0x8004DDC6, "Timeout occured on secure bus while waiting for DOC to become empty.")
    DRM_E_SECUREBUS_READ_FAILED = (0x8004DDC7, "Read request on secure bus failed.")
    DRM_E_MUTEX_OWNERSHIP_MATCH_FAILED = (0x8004DDC8, "Token ID reserved for the mutex in hardware doesn't match with specified token ID.")
    DRM_E_INVALID_PDI = (0x8004DDC9, "The read PDI value is invalid.")
    DRM_E_SECURETIME_INVALID_REQUEST_DATA = (0x8004DE00, "The secure time client request data is invalid.")
    DRM_E_SECURETIME_CLOCK_NOT_SET = (0x8004DE01, "The secure time clock has not been set.")
    DRM_E_SECURETIME_RESPONSE_TIMEOUT = (0x8004DE02, "The secure time server response timed out.")
    DRM_E_SECURETIME_SERVER_SECURITY_LEVEL_TOO_LOW = (0x8004DE03, "The secure time server's security level is too low for the client.")
    DRM_E_LICENSESERVERTIME_MUST_REACQUIRE_LICENSE = (0x8004DE04, "This license was acquired before the LicenseServerTime feature was enabled.  It must be reacquired.")
    DRM_E_LSRD_DETECTED = (0x8004DF00, "HDS file rollback is detected.")
    DRM_E_LSRD_INVALID_ACL = (0x8004DF01, "The ACL of the HDS Registry Subkey is invalid.")
    DRM_E_LSRD_DETECTION_IN_PROGRESS = (0x8004DF02, "The client is currently processing LSRD check operation. Concurrent operations are not allowed.")
    DRM_E_LSRD_ACL_NOT_PRESENT = (0x8004DF03, "The security descriptor does not contain an ACL.")
    DRM_E_LSRD_INVALID_COMMAND = (0x8004DF04, "The PlayReady Process received an invalid command.")
    DRM_E_LSRD_SEQUENCE_NUMBER_IS_AT_MAX_LIMIT = (0x8004DF05, "The LSRD sequence number has reached its maximum limit.")
    DRM_E_SECUREDELETE_INVALID_RESPONSE = (0x8004DFA0, "The secure delete response is invalid.")
    DRM_E_PROVENANCE_VALIDATION_FAILED = (0x8004DFB0, "The provenance validation failed. The media file has been tampered with.")
    DRM_E_INVALID_PROVENANCE_MANIFEST = (0x8004DFB1, "The provenance manifest is invalid.")
    DRM_E_INVALID_PROVENANCE_CERTIFICATE_CHAIN = (0x8004DFB2, "The provenance certificate chain stored in the manifest is invalid or a valid certificate chain could not be established.")
    DRM_E_PROVENANCE_UNTRUSTED_ROOT_CERTIFICATE = (0x8004DFB3, "The provenance certificate chain could not be validated because no root certificates were provided in the trusted list.")
    DRM_E_MP4_EXCEEDED_NUM_CHUNKS = (0x8004DFB4, "A query was made to the MP4 parser to get chunk information for a chunk that does not exist.")
    DRM_E_MP4_NULL_FILE_STREAM = (0x8004DFB5, "A file stream pointer was unexpectedly null.")
    DRM_E_MP4_INVALID_MP4_FILE = (0x8004DFB6, "The MP4 file is malformed.")
    DRM_E_MP4_PARSING_ABORTED = (0x8004DFB7, "MP4 parsing was aborted by the caller.")
    DRM_E_MP4_EXCEEDED_BOX_SIZE = (0x8004DFB8, "The MP4 file has a box that references data beyond the end of the box.")
    DRM_E_MP4_INVALID_BOX_SIZE = (0x8004DFB9, "The MP4 file has an invalid box size.")
    DRM_E_MP4_INVALID_PARSING_STATE = (0x8004DFBA, "MP4 parser functions were invoked in an invalid sequence.")
    DRM_E_MP4_INVALID_BOX_ATTRIBUTE = (0x8004DFBB, "An MP4 box has a malformed attribute.")
    DRM_E_MP4_INVALID_BOX_VERSION = (0x8004DFBC, "An MP4 box had an unrecognized version.")
    DRM_E_MP4_INVALID_STTS_CONTAINS_ENTRIES = (0x8004DFBD, "The 'stts' box should not contain entries in purely fragmented Mp4 files.")
    DRM_E_C2PA_FTYP_NOT_SET = (0x8004DFBE, "The 'ftyp' box lacks the 'c2pa' compatible_brands attribute.")
    DRM_E_MP4_BOX_LARGER_THAN_4GB = (0x8004DFBF, "The MP4 file has a box that is larger than 4 GB in size which is not supported by this parsre.")
    DRM_E_MP4_C2PA_BOX_ALREADY_PRESENT = (0x8004DFC0, "The MP4 file already contains an unexpected C2PA Box.")
    DRM_E_MP4_CIB_BOX_ALREADY_PRESENT = (0x8004DFC1, "The MP4 file already contains an unexpected Content Integrity Box.")
    DRM_E_C2PA_MANIFEST_BOX_NOT_PRESENT = (0x8004DFC2, "The MP4 file lacks the expected c2pa Manifest Box.")
    DRM_E_C2PA_MERKLE_BOX_NOT_PRESENT = (0x8004DFC3, "The MP4 file lacks the expected c2pa Merkle Box.")
    DRM_E_MP4_INVALID_C2PA_MANIFEST_BOX = (0x8004DFC4, "The MP4 file contains an invalid c2pa box with type Manifest.")
    DRM_E_MP4_INVALID_C2PA_MERKLE_BOX = (0x8004DFC5, "The MP4 file contains an invalid c2pa box with type Merkle.")
    DRM_E_MP4_INVALID_PARSING_TYPE = (0x8004DFC6, "The MP4 parser was initialized with an invalid type.")
    DRM_E_MP4_FILE_LACKS_MOOV_BOX = (0x8004DFC7, "The MP4 file does not have a 'moov' box.")
    DRM_E_MP4_EXCEEDED_NUM_TRACK_IDS = (0x8004DFC8, "A query was made to the MP4 parser to get track information for a track that does not exist.")
    DRM_E_MP4_INVALID_EXCLUSION_RULE = (0x8004DFC9, "An Exclusion Rule was passed into the MP4 Parser that was incorrectly formatted.")
    DRM_E_WIN32_FILE_NOT_FOUND = (0x80070002, "The system cannot find the file specified.")
    DRM_E_HANDLE = (0x80070006, "Invalid handle.")
    DRM_E_WIN32_NO_MORE_FILES = (0x80070012, "There are no more files.")
    DRM_E_INVALIDARG = (0x80070057, "The parameter is incorrect.")
    DRM_E_BUFFERTOOSMALL = (0x8007007A, "The data area passed to a function is too small.")
    DRM_E_NOMORE = (0x80070103, "No more data is available.")
    DRM_E_ARITHMETIC_OVERFLOW = (0x80070216, "Arithmetic result exceeded maximum value.")
    DRM_E_NOT_FOUND = (0x80070490, "Element not found.")
    DRM_E_INVALID_COMMAND_LINE = (0x80070667, "Invalid command line argument.")
    DRM_E_FAILED_TO_STORE_LICENSE = (0xC00D2712, "License storage is not working.")
    DRM_E_PARAMETERS_MISMATCHED = (0xC00D272F, "A problem has occurred in the Digital Rights Management component.")
    DRM_E_NOT_ALL_STORED = (0xC00D275F, "Some of the licenses could not be stored.")

    @property
    def code(self):
        return hex(self.value[0])

    @property
    def message(self):
        return self.value[1]

    @staticmethod
    def from_code(code: str):
        for error in DrmResult:
            if error.value[0] == int(code, 16):
                return error
        raise ValueError("Invalid DRMResult")

import xml.etree.ElementTree as ET

class Util:
    @staticmethod
    def remove_namespaces(element: ET.Element) -> None:
        for elem in element.iter():
            elem.tag = elem.tag.split('}')[-1]

    @staticmethod
    def un_pad(name: bytes) -> str:
        return name.rstrip(b'\x00').decode("utf-8", errors="ignore")

    @staticmethod
    def to_bytes(n: int) -> bytes:
        byte_len = (n.bit_length() + 7) // 8
        if byte_len % 2 != 0:
            byte_len += 1
        return n.to_bytes(byte_len, 'big')

import base64
from pathlib import Path
from typing import Union

from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.PublicKey.ECC import EccKey
from ecpy.curves import Curve, Point

class ECCKey:
    def __init__(self, key: EccKey):
        self.key = key

    @classmethod
    def generate(cls):
        return cls(key=ECC.generate(curve='P-256'))

    @classmethod
    def construct(cls, private_key: Union[bytes, int]):
        if isinstance(private_key, bytes):
            private_key = int.from_bytes(private_key, 'big')
        if not isinstance(private_key, int):
            raise ValueError(f"Expecting Bytes or Int input, got {private_key!r}")

        key = ECC.construct(curve='P-256',
                            d=private_key)

        return cls(key=key)

    @classmethod
    def loads(cls, data: Union[str, bytes]) -> ECCKey:
        if isinstance(data, str):
            data = base64.b64decode(data)
        if not isinstance(data, bytes):
            raise ValueError(f"Expecting Bytes or Base64 input, got {data!r}")

        if len(data) not in [96, 32]:
            raise ValueError(f"Invalid data length. Expecting 96 or 32 bytes, got {len(data)}")

        return cls.construct(private_key=data[:32])

    @classmethod
    def load(cls, path: Union[Path, str]) -> ECCKey:
        if not isinstance(path, (Path, str)):
            raise ValueError(f"Expecting Path object or path string, got {path!r}")
        with Path(path).open(mode="rb") as f:
            return cls.loads(f.read())

    def dumps(self, private_only=False):
        if private_only:
            return self.private_bytes()
        return self.private_bytes() + self.public_bytes()

    def dump(self, path: Union[Path, str], private_only=False) -> None:
        if not isinstance(path, (Path, str)):
            raise ValueError(f"Expecting Path object or path string, got {path!r}")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.dumps(private_only))

    def get_point(self, curve: Curve) -> Point:
        return Point(self.key.pointQ.x, self.key.pointQ.y, curve)

    def private_bytes(self) -> bytes:
        return Util.to_bytes(int(self.key.d))

    def private_sha256_digest(self) -> bytes:
        hash_object = SHA256.new()
        hash_object.update(self.private_bytes())
        return hash_object.digest()

    def public_bytes(self) -> bytes:
        return Util.to_bytes(int(self.key.pointQ.x)) + Util.to_bytes(int(self.key.pointQ.y))

    def public_sha256_digest(self) -> bytes:
        hash_object = SHA256.new()
        hash_object.update(self.public_bytes())
        return hash_object.digest()

from typing import Tuple
from ecpy.curves import Curve, Point
import secrets

class ElGamal:
    curve = Curve.get_curve("secp256r1")

    @staticmethod
    def encrypt(message_point: Point, public_key: Point) -> Tuple[Point, Point]:
        ephemeral_key = secrets.randbelow(ElGamal.curve.order)
        point1 = ephemeral_key * ElGamal.curve.generator
        point2 = message_point + (ephemeral_key * public_key)
        return point1, point2

    @staticmethod
    def decrypt(encrypted: Tuple[Point, Point], private_key: int) -> Point:
        point1, point2 = encrypted
        shared_secret = private_key * point1
        decrypted_message = point2 - shared_secret
        return decrypted_message

from Crypto.Cipher import AES
from Crypto.Hash import CMAC
from cryptography.hazmat.primitives.keywrap import aes_key_unwrap

def derive_wrapping_key() -> bytes:
    KeyDerivationCertificatePrivateKeysWrap = bytes([
        0x9c, 0xe9, 0x34, 0x32, 0xc7, 0xd7, 0x40, 0x16,
        0xba, 0x68, 0x47, 0x63, 0xf8, 0x01, 0xe1, 0x36
    ])

    CTK_TEST = bytes([
        0x8B, 0x22, 0x2F, 0xFD, 0x1E, 0x76, 0x19, 0x56,
        0x59, 0xCF, 0x27, 0x03, 0x89, 0x8C, 0x42, 0x7F
    ])

    cmac = CMAC.new(CTK_TEST, ciphermod=AES)

    cmac.update(bytes([
        1,
        *KeyDerivationCertificatePrivateKeysWrap,
        0,
        *bytes(16),
        0, 128
    ]))

    derived_wrapping_key = cmac.digest()

    return derived_wrapping_key

def unwrap_wrapped_key(wrapped_key: bytes) -> bytes:
    wrapping_key = derive_wrapping_key()
    unwrapped_key = aes_key_unwrap(wrapping_key, wrapped_key)

    return unwrapped_key[:32]

from construct import Struct, Const, Int8ub, Bytes, this, Int32ub, Switch, Embedded

class DeviceStructs:
    magic = Const(b"PRD")

    v1 = Struct(
        "group_key_length" / Int32ub,
        "group_key" / Bytes(this.group_key_length),
        "group_certificate_length" / Int32ub,
        "group_certificate" / Bytes(this.group_certificate_length)
    )

    v2 = Struct(
        "group_certificate_length" / Int32ub,
        "group_certificate" / Bytes(this.group_certificate_length),
        "encryption_key" / Bytes(96),
        "signing_key" / Bytes(96)
    )

    v3 = Struct(
        "group_key" / Bytes(96),
        "encryption_key" / Bytes(96),
        "signing_key" / Bytes(96),
        "group_certificate_length" / Int32ub,
        "group_certificate" / Bytes(this.group_certificate_length)
    )

    prd = Struct(
        "signature" / magic,
        "version" / Int8ub,
        Embedded(Switch(
            lambda ctx: ctx.version,
            {
                1: v1,
                2: v2,
                3: v3
            }
        ))
    )

import collections.abc

if not hasattr(collections, 'Sequence'):
    collections.Sequence = collections.abc.Sequence

import time
import base64
from pathlib import Path
from typing import Union, Optional
from enum import IntEnum

from Crypto.PublicKey import ECC

from construct import Bytes, Const, Int32ub, GreedyRange, Switch, Container, ListContainer, Embedded
from construct import Int16ub, Array
from construct import Struct, this

class BCertCertType(IntEnum):
    UNKNOWN = 0x00000000
    PC = 0x00000001
    DEVICE = 0x00000002
    DOMAIN = 0x00000003
    ISSUER = 0x00000004
    CRL_SIGNER = 0x00000005
    SERVICE = 0x00000006
    SILVERLIGHT = 0x00000007
    APPLICATION = 0x00000008
    METERING = 0x00000009
    KEYFILESIGNER = 0x0000000a
    SERVER = 0x0000000b
    LICENSESIGNER = 0x0000000c
    SECURETIMESERVER = 0x0000000d
    RPROVMODELAUTH = 0x0000000e

class BCertObjType(IntEnum):
    BASIC = 0x0001
    DOMAIN = 0x0002
    PC = 0x0003
    DEVICE = 0x0004
    FEATURE = 0x0005
    KEY = 0x0006
    MANUFACTURER = 0x0007
    SIGNATURE = 0x0008
    SILVERLIGHT = 0x0009
    METERING = 0x000A
    EXTDATASIGNKEY = 0x000B
    EXTDATACONTAINER = 0x000C
    EXTDATASIGNATURE = 0x000D
    EXTDATA_HWID = 0x000E
    SERVER = 0x000F
    SECURITY_VERSION = 0x0010
    SECURITY_VERSION_2 = 0x0011
    UNKNOWN_OBJECT_ID = 0xFFFD

class BCertFlag(IntEnum):
    EMPTY = 0x00000000
    EXTDATA_PRESENT = 0x00000001

class BCertObjFlag(IntEnum):
    EMPTY = 0x0000
    MUST_UNDERSTAND = 0x0001
    CONTAINER_OBJ = 0x0002

class BCertSignatureType(IntEnum):
    P256 = 0x0001

class BCertKeyType(IntEnum):
    ECC256 = 0x0001

class BCertKeyUsage(IntEnum):
    UNKNOWN = 0x00000000
    SIGN = 0x00000001
    ENCRYPT_KEY = 0x00000002
    SIGN_CRL = 0x00000003
    ISSUER_ALL = 0x00000004
    ISSUER_INDIV = 0x00000005
    ISSUER_DEVICE = 0x00000006
    ISSUER_LINK = 0x00000007
    ISSUER_DOMAIN = 0x00000008
    ISSUER_SILVERLIGHT = 0x00000009
    ISSUER_APPLICATION = 0x0000000a
    ISSUER_CRL = 0x0000000b
    ISSUER_METERING = 0x0000000c
    ISSUER_SIGN_KEYFILE = 0x0000000d
    SIGN_KEYFILE = 0x0000000e
    ISSUER_SERVER = 0x0000000f
    ENCRYPTKEY_SAMPLE_PROTECTION_RC4 = 0x00000010
    RESERVED2 = 0x00000011
    ISSUER_SIGN_LICENSE = 0x00000012
    SIGN_LICENSE = 0x00000013
    SIGN_RESPONSE = 0x00000014
    PRND_ENCRYPT_KEY_DEPRECATED = 0x00000015
    ENCRYPTKEY_SAMPLE_PROTECTION_AES128CTR = 0x00000016
    ISSUER_SECURETIMESERVER = 0x00000017
    ISSUER_RPROVMODELAUTH = 0x00000018

class BCertFeatures(IntEnum):
    TRANSMITTER = 0x00000001
    RECEIVER = 0x00000002
    SHARED_CERTIFICATE = 0x00000003
    SECURE_CLOCK = 0x00000004
    ANTIROLLBACK_CLOCK = 0x00000005
    RESERVED_METERING = 0x00000006
    RESERVED_LICSYNC = 0x00000007
    RESERVED_SYMOPT = 0x00000008
    SUPPORTS_CRLS = 0x00000009
    SERVER_BASIC_EDITION = 0x0000000A
    SERVER_STANDARD_EDITION = 0x0000000B
    SERVER_PREMIUM_EDITION = 0x0000000C
    SUPPORTS_PR3_FEATURES = 0x0000000D
    DEPRECATED_SECURE_STOP = 0x0000000E

class _BCertStructs:
    Header = Struct(
        "flags" / Int16ub,
        "tag" / Int16ub,
        "length" / Int32ub,
    )

    BasicInfo = Struct(
        "cert_id" / Bytes(16),
        "security_level" / Int32ub,
        "flags" / Int32ub,
        "cert_type" / Int32ub,
        "public_key_digest" / Bytes(32),
        "expiration_date" / Int32ub,
        "client_id" / Bytes(16)
    )

    DomainInfo = Struct(
        "service_id" / Bytes(16),
        "account_id" / Bytes(16),
        "revision_timestamp" / Int32ub,
        "domain_url_length" / Int32ub,
        "domain_url" / Bytes((this.domain_url_length + 3) & 0xfffffffc)
    )

    PCInfo = Struct(
        "security_version" / Int32ub
    )

    DeviceInfo = Struct(
        "max_license" / Int32ub,
        "max_header" / Int32ub,
        "max_chain_depth" / Int32ub
    )

    FeatureInfo = Struct(
        "feature_count" / Int32ub,
        "features" / Array(this.feature_count, Int32ub)
    )

    KeyInfo = Struct(
        "key_count" / Int32ub,
        "cert_keys" / Array(this.key_count, Struct(
            "type" / Int16ub,
            "length" / Int16ub,
            "flags" / Int32ub,
            "key" / Bytes(this.length // 8),
            "usages_count" / Int32ub,
            "usages" / Array(this.usages_count, Int32ub)
        ))
    )

    ManufacturerInfo = Struct(
        "flags" / Int32ub,
        "manufacturer_name_length" / Int32ub,
        "manufacturer_name" / Bytes((this.manufacturer_name_length + 3) & 0xfffffffc),
        "model_name_length" / Int32ub,
        "model_name" / Bytes((this.model_name_length + 3) & 0xfffffffc),
        "model_number_length" / Int32ub,
        "model_number" / Bytes((this.model_number_length + 3) & 0xfffffffc),
    )

    SignatureInfo = Struct(
        "signature_type" / Int16ub,
        "signature_size" / Int16ub,
        "signature" / Bytes(this.signature_size),
        "signature_key_size" / Int32ub,
        "signature_key" / Bytes(this.signature_key_size // 8)
    )

    SilverlightInfo = Struct(
        "security_version" / Int32ub,
        "platform_identifier" / Int32ub
    )

    MeteringInfo = Struct(
        "metering_id" / Bytes(16),
        "metering_url_length" / Int32ub,
        "metering_url" / Bytes((this.metering_url_length + 3) & 0xfffffffc)
    )

    ExtDataSignKeyInfo = Struct(
        "key_type" / Int16ub,
        "key_length" / Int16ub,
        "flags" / Int32ub,
        "key" / Bytes(this.key_length // 8)
    )

    DataRecord = Struct(
        "data_size" / Int32ub,
        "data" / Bytes(this.data_size)
    )

    ExtDataSignature = Struct(
        "signature_type" / Int16ub,
        "signature_size" / Int16ub,
        "signature" / Bytes(this.signature_size)
    )

    ExtDataHwid = Struct(
        "record_length" / Int32ub,
        "record_data" / Bytes(this.record_length),
        "padding" / Bytes((4 - (this.record_length % 4)) % 4)
    )

    ExtDataContainer = Struct(
        "record" / Struct(
            Embedded(Header),
            Embedded(ExtDataHwid)
        ),
        "signature" / Struct(
            Embedded(Header),
            Embedded(ExtDataSignature)
        )
    )

    ServerInfo = Struct(
        "warning_days" / Int32ub
    )

    SecurityVersion = Struct(
        "security_version" / Int32ub,
        "platform_identifier" / Int32ub
    )

    Attribute = Struct(
        Embedded(Header),
        "attribute" / Switch(
            lambda this_: this_.tag,
            {
                BCertObjType.BASIC: BasicInfo,
                BCertObjType.DOMAIN: DomainInfo,
                BCertObjType.PC: PCInfo,
                BCertObjType.DEVICE: DeviceInfo,
                BCertObjType.FEATURE: FeatureInfo,
                BCertObjType.KEY: KeyInfo,
                BCertObjType.MANUFACTURER: ManufacturerInfo,
                BCertObjType.SIGNATURE: SignatureInfo,
                BCertObjType.SILVERLIGHT: SilverlightInfo,
                BCertObjType.METERING: MeteringInfo,
                BCertObjType.EXTDATASIGNKEY: ExtDataSignKeyInfo,
                BCertObjType.EXTDATACONTAINER: ExtDataContainer,
                BCertObjType.SERVER: ServerInfo,
                BCertObjType.SECURITY_VERSION: SecurityVersion,
                BCertObjType.SECURITY_VERSION_2: SecurityVersion
            },
            default=Bytes(this.length - 8)
        )
    )

    BCert = Struct(
        "signature" / Const(b"CERT"),
        "version" / Int32ub,
        "total_length" / Int32ub,
        "certificate_length" / Int32ub,
        "attributes" / GreedyRange(Attribute)
    )

    BCertChain = Struct(
        "signature" / Const(b"CHAI"),
        "version" / Int32ub,
        "total_length" / Int32ub,
        "flags" / Int32ub,
        "certificate_count" / Int32ub,
        "certificates" / GreedyRange(BCert)
    )

class Certificate(_BCertStructs):

    def __init__(
            self,
            parsed_bcert: Container,
            bcert_obj: _BCertStructs.BCert = _BCertStructs.BCert
    ):
        self.parsed = parsed_bcert
        self._BCERT = bcert_obj

    @classmethod
    def new_leaf_cert(
            cls,
            cert_id: bytes,
            security_level: int,
            client_id: bytes,
            signing_key: ECCKey,
            encryption_key: ECCKey,
            group_key: ECCKey,
            parent: CertificateChain,
            expiry: int = 0xFFFFFFFF
    ) -> Certificate:
        basic_info = Container(
            cert_id=cert_id,
            security_level=security_level,
            flags=BCertFlag.EMPTY,
            cert_type=BCertCertType.DEVICE,
            public_key_digest=signing_key.public_sha256_digest(),
            expiration_date=expiry,
            client_id=client_id
        )
        basic_info_attribute = Container(
            flags=BCertObjFlag.MUST_UNDERSTAND,
            tag=BCertObjType.BASIC,
            length=len(_BCertStructs.BasicInfo.build(basic_info)) + 8,
            attribute=basic_info
        )

        device_info = Container(
            max_license=10240,
            max_header=15360,
            max_chain_depth=2
        )
        device_info_attribute = Container(
            flags=BCertObjFlag.MUST_UNDERSTAND,
            tag=BCertObjType.DEVICE,
            length=len(_BCertStructs.DeviceInfo.build(device_info)) + 8,
            attribute=device_info
        )

        feature = Container(
            feature_count=3,
            features=ListContainer([
                BCertFeatures.SECURE_CLOCK,
                BCertFeatures.SUPPORTS_CRLS,
                BCertFeatures.SUPPORTS_PR3_FEATURES
            ])
        )
        feature_attribute = Container(
            flags=BCertObjFlag.MUST_UNDERSTAND,
            tag=BCertObjType.FEATURE,
            length=len(_BCertStructs.FeatureInfo.build(feature)) + 8,
            attribute=feature
        )

        signing_key_public_bytes = signing_key.public_bytes()
        cert_key_sign = Container(
            type=BCertKeyType.ECC256,
            length=len(signing_key_public_bytes) * 8,
            flags=BCertFlag.EMPTY,
            key=signing_key_public_bytes,
            usages_count=1,
            usages=ListContainer([
                BCertKeyUsage.SIGN
            ])
        )

        encryption_key_public_bytes = encryption_key.public_bytes()
        cert_key_encrypt = Container(
            type=BCertKeyType.ECC256,
            length=len(encryption_key_public_bytes) * 8,
            flags=BCertFlag.EMPTY,
            key=encryption_key_public_bytes,
            usages_count=1,
            usages=ListContainer([
                BCertKeyUsage.ENCRYPT_KEY
            ])
        )

        key_info = Container(
            key_count=2,
            cert_keys=ListContainer([
                cert_key_sign,
                cert_key_encrypt
            ])
        )
        key_info_attribute = Container(
            flags=BCertObjFlag.MUST_UNDERSTAND,
            tag=BCertObjType.KEY,
            length=len(_BCertStructs.KeyInfo.build(key_info)) + 8,
            attribute=key_info
        )

        manufacturer_info = parent.get(0).get_attribute(BCertObjType.MANUFACTURER)

        new_bcert_container = Container(
            signature=b"CERT",
            version=1,
            total_length=0,
            certificate_length=0,
            attributes=ListContainer([
                basic_info_attribute,
                device_info_attribute,
                feature_attribute,
                key_info_attribute,
                manufacturer_info,
            ])
        )

        payload = _BCertStructs.BCert.build(new_bcert_container)
        new_bcert_container.certificate_length = len(payload)
        new_bcert_container.total_length = len(payload) + 144

        sign_payload = _BCertStructs.BCert.build(new_bcert_container)
        signature = Crypto.ecc256_sign(group_key, sign_payload)

        group_key_public_bytes = group_key.public_bytes()

        signature_info = Container(
            signature_type=BCertSignatureType.P256,
            signature_size=len(signature),
            signature=signature,
            signature_key_size=len(group_key_public_bytes) * 8,
            signature_key=group_key_public_bytes
        )
        signature_info_attribute = Container(
            flags=BCertObjFlag.MUST_UNDERSTAND,
            tag=BCertObjType.SIGNATURE,
            length=len(_BCertStructs.SignatureInfo.build(signature_info)) + 8,
            attribute=signature_info
        )
        new_bcert_container.attributes.append(signature_info_attribute)

        return cls(new_bcert_container)

    @classmethod
    def loads(cls, data: Union[str, bytes]) -> Certificate:
        if isinstance(data, str):
            data = base64.b64decode(data)
        if not isinstance(data, bytes):
            raise ValueError(f"Expecting Bytes or Base64 input, got {data!r}")

        cert = _BCertStructs.BCert
        return cls(
            parsed_bcert=cert.parse(data),
            bcert_obj=cert
        )

    def get_attribute(self, type_: int) -> Optional[Container]:
        for attribute in self.parsed.attributes:
            if attribute.tag == type_:
                return attribute

        return None

    def get_security_level(self) -> Optional[int]:
        basic_info = self.get_attribute(BCertObjType.BASIC)
        if basic_info:
            return basic_info.attribute.security_level

        return None

    def get_name(self) -> Optional[str]:
        manufacturer_info_attr = self.get_attribute(BCertObjType.MANUFACTURER)

        if manufacturer_info_attr:
            manufacturer_info = manufacturer_info_attr.attribute

            manufacturer = Util.un_pad(manufacturer_info.manufacturer_name)
            model_name = Util.un_pad(manufacturer_info.model_name)
            model_number = Util.un_pad(manufacturer_info.model_number)

            return f"{manufacturer} {model_name} {model_number}"

        return None

    def get_type(self) -> Optional[int]:
        basic_info = self.get_attribute(BCertObjType.BASIC)
        if basic_info:
            return basic_info.attribute.cert_type

        return None

    def get_expiration_date(self) -> Optional[int]:
        basic_info = self.get_attribute(BCertObjType.BASIC)
        if basic_info:
            return basic_info.attribute.expiration_date

        return None

    def get_issuer_key(self) -> Optional[bytes]:
        signature_object = self.get_attribute(BCertObjType.SIGNATURE)
        if not signature_object:
            return None

        return signature_object.attribute.signature_key

    def get_key_by_usage(self, key_usage: BCertKeyUsage) -> Optional[bytes]:
        key_info_object = self.get_attribute(BCertObjType.KEY)
        if not key_info_object:
            return None

        for key in key_info_object.attribute.cert_keys:
            for usage in key.usages:
                if usage == key_usage:
                    return key.key

        return None

    def contains_public_key(self, public_key: Union[ECCKey, bytes]) -> bool:
        if isinstance(public_key, ECCKey):
            public_key = public_key.public_bytes()

        key_info_object = self.get_attribute(BCertObjType.KEY)
        if not key_info_object:
            return False

        for key in key_info_object.attribute.cert_keys:
            if key.key == public_key:
                return True

        return False

    def dumps(self) -> bytes:
        return self._BCERT.build(self.parsed)

    def _verify_extdata_signature(self) -> None:
        sign_key = self.get_attribute(BCertObjType.EXTDATASIGNKEY)
        if not sign_key:
            raise InvalidCertificate("No extdata sign key object found in certificate")

        sign_key_bytes = sign_key.attribute.key

        signing_key = ECC.construct(
            point_x=int.from_bytes(sign_key_bytes[:32], "big"),
            point_y=int.from_bytes(sign_key_bytes[32:], "big"),
            curve="P-256"
        )

        extdata = self.get_attribute(BCertObjType.EXTDATACONTAINER)
        if not extdata:
            raise InvalidCertificate("No extdata container found in certificate")

        signature = extdata.attribute.signature.signature

        sign_data = _BCertStructs.ExtDataContainer.subcons[0].build(extdata.attribute.record)

        if not Crypto.ecc256_verify(
            public_key=signing_key,
            data=sign_data,
            signature=signature
        ):
            raise InvalidCertificate("Signature of certificate extdata is not authentic")

    def verify_signature(self) -> None:
        signature_object = self.get_attribute(BCertObjType.SIGNATURE)
        if not signature_object:
            raise InvalidCertificate("No signature object found in certificate")

        signature_attribute = signature_object.attribute
        raw_signature_key = signature_attribute.signature_key

        signature_key = ECC.construct(
            curve='P-256',
            point_x=int.from_bytes(raw_signature_key[:32], 'big'),
            point_y=int.from_bytes(raw_signature_key[32:], 'big')
        )

        sign_payload = self.dumps()[:self.parsed.certificate_length]

        if not Crypto.ecc256_verify(
            public_key=signature_key,
            data=sign_payload,
            signature=signature_attribute.signature
        ):
            raise InvalidCertificate("Signature of certificate is not authentic")

        basic_info_attribute = self.get_attribute(BCertObjType.BASIC)
        if not basic_info_attribute:
            raise InvalidCertificate("No basic info object found in certificate")

        if basic_info_attribute.attribute.flags & BCertFlag.EXTDATA_PRESENT == BCertFlag.EXTDATA_PRESENT:
            self._verify_extdata_signature()

class CertificateChain(_BCertStructs):
    MSPlayReadyRootIssuerPubKey = bytes([
        0x86, 0x4D, 0x61, 0xCF, 0xF2, 0x25, 0x6E, 0x42, 0x2C, 0x56, 0x8B, 0x3C, 0x28, 0x00, 0x1C, 0xFB,
        0x3E, 0x15, 0x27, 0x65, 0x85, 0x84, 0xBA, 0x05, 0x21, 0xB7, 0x9B, 0x18, 0x28, 0xD9, 0x36, 0xDE,
        0x1D, 0x82, 0x6A, 0x8F, 0xC3, 0xE6, 0xE7, 0xFA, 0x7A, 0x90, 0xD5, 0xCA, 0x29, 0x46, 0xF1, 0xF6,
        0x4A, 0x2E, 0xFB, 0x9F, 0x5D, 0xCF, 0xFE, 0x7E, 0x43, 0x4E, 0xB4, 0x42, 0x93, 0xFA, 0xC5, 0xAB
    ])

    def __init__(
            self,
            parsed_bcert_chain: Container,
            bcert_chain_obj: _BCertStructs.BCertChain = _BCertStructs.BCertChain
    ):
        self.parsed = parsed_bcert_chain
        self._BCERT_CHAIN = bcert_chain_obj

    @classmethod
    def loads(cls, data: Union[str, bytes]) -> CertificateChain:
        if isinstance(data, str):
            data = base64.b64decode(data)
        if not isinstance(data, bytes):
            raise ValueError(f"Expecting Bytes or Base64 input, got {data!r}")

        cert_chain = _BCertStructs.BCertChain
        return cls(
            parsed_bcert_chain=cert_chain.parse(data),
            bcert_chain_obj=cert_chain
        )

    @classmethod
    def load(cls, path: Union[Path, str]) -> CertificateChain:
        if not isinstance(path, (Path, str)):
            raise ValueError(f"Expecting Path object or path string, got {path!r}")
        with Path(path).open(mode="rb") as f:
            return cls.loads(f.read())

    def dumps(self) -> bytes:
        return self._BCERT_CHAIN.build(self.parsed)

    def get_security_level(self) -> int:
        return self.get(0).get_security_level()

    def get_name(self) -> str:
        return self.get(0).get_name()

    def verify_chain(
            self,
            check_expiry: bool = False,
            cert_type: Optional[BCertCertType] = None
    ) -> bool:
        if not (1 <= self.count() <= 6):
            raise InvalidCertificateChain("An invalid maximum license chain depth")

        for i in range(self.count()):
            if i == 0 and cert_type:
                if self.get(i).get_type() != cert_type:
                    raise InvalidCertificateChain("Invalid certificate type")

            self.get(i).verify_signature()

            if check_expiry:
                if time.time() >= self.get(i).get_expiration_date():
                    raise InvalidCertificateChain(f"Certificate {i} has expired")

            if i > 0:
                if not self._verify_adjacent_certs(self.get(i - 1), self.get(i)):
                    raise InvalidCertificateChain("Adjacent certificate validation failed")

            if i == (self.count() - 1):
                if self.get(i).get_issuer_key() != self.MSPlayReadyRootIssuerPubKey:
                    raise InvalidCertificateChain("Root certificate issuer missmatch")

        return True

    @staticmethod
    def _verify_adjacent_certs(child_cert: Certificate, parent_cert: Certificate) -> bool:
        if parent_cert.get_type() != BCertCertType.ISSUER:
            return False

        if child_cert.get_security_level() > parent_cert.get_expiration_date():
            return False

        key_info = parent_cert.get_attribute(BCertObjType.KEY)
        if not key_info:
            return False

        issuer_key = child_cert.get_issuer_key()

        issuer_key_match = False
        for key in key_info.attribute.cert_keys:
            if key.key == issuer_key:
                issuer_key_match = True

        if not issuer_key_match:
            return False

        return True

    def append(self, bcert: Certificate) -> None:
        self.parsed.certificate_count += 1
        self.parsed.certificates.append(bcert.parsed)
        self.parsed.total_length += len(bcert.dumps())

    def prepend(self, bcert: Certificate) -> None:
        self.parsed.certificate_count += 1
        self.parsed.certificates.insert(0, bcert.parsed)
        self.parsed.total_length += len(bcert.dumps())

    def remove(self, index: int) -> None:
        if self.count() <= 0:
            raise InvalidCertificateChain("CertificateChain does not contain any Certificates")
        if index >= self.count():
            raise IndexError(f"No Certificate at index {index}, {self.count()} total")

        self.parsed.certificate_count -= 1
        self.parsed.total_length -= len(self.get(index).dumps())
        self.parsed.certificates.pop(index)

    def get(self, index: int) -> Certificate:
        if self.count() <= 0:
            raise InvalidCertificateChain("CertificateChain does not contain any Certificates")
        if index >= self.count():
            raise IndexError(f"No Certificate at index {index}, {self.count()} total")

        return Certificate(self.parsed.certificates[index])

    def count(self) -> int:
        return self.parsed.certificate_count

import base64
from enum import IntEnum
from pathlib import Path
from typing import Union, Any, Optional

class Device:
    CURRENT_VERSION = 3

    class SecurityLevel(IntEnum):
        SL150 = 150
        SL2000 = 2000
        SL3000 = 3000

    def __init__(
            self,
            *_: Any,
            group_key: Optional[str, bytes, None],
            encryption_key: Union[str, bytes],
            signing_key: Union[str, bytes],
            group_certificate: Union[str, bytes],
            **__: Any
    ):
        if isinstance(group_key, str):
            group_key = base64.b64decode(group_key)

        if isinstance(encryption_key, str):
            encryption_key = base64.b64decode(encryption_key)
        if not isinstance(encryption_key, bytes):
            raise ValueError(f"Expecting Bytes or Base64 input, got {encryption_key!r}")

        if isinstance(signing_key, str):
            signing_key = base64.b64decode(signing_key)
        if not isinstance(signing_key, bytes):
            raise ValueError(f"Expecting Bytes or Base64 input, got {signing_key!r}")

        if isinstance(group_certificate, str):
            group_certificate = base64.b64decode(group_certificate)
        if not isinstance(group_certificate, bytes):
            raise ValueError(f"Expecting Bytes or Base64 input, got {group_certificate!r}")

        self.group_key = None if group_key is None else ECCKey.loads(group_key)
        self.encryption_key = ECCKey.loads(encryption_key)
        self.signing_key = ECCKey.loads(signing_key)
        self.group_certificate = CertificateChain.loads(group_certificate)
        self.security_level = self.group_certificate.get_security_level()

    @classmethod
    def loads(cls, data: Union[str, bytes]) -> Device:
        if isinstance(data, str):
            data = base64.b64decode(data)
        if not isinstance(data, bytes):
            raise ValueError(f"Expecting Bytes or Base64 input, got {data!r}")

        parsed = DeviceStructs.prd.parse(data)
        return cls(**{
            **parsed,
            'group_key': parsed.get('group_key', None)
        })

    @classmethod
    def load(cls, path: Union[Path, str]) -> Device:
        if not isinstance(path, (Path, str)):
            raise ValueError(f"Expecting Path object or path string, got {path!r}")
        with Path(path).open(mode="rb") as f:
            return cls.loads(f.read())

    def dumps(self, version: int = CURRENT_VERSION) -> bytes:
        if self.group_key is None and version == self.CURRENT_VERSION:
            raise OutdatedDevice("Cannot dump device as version 3 without having a group key. Either provide a group key or set argument version=2")

        return DeviceStructs.prd.build(dict(
            version=version,
            group_key=self.group_key.dumps() if self.group_key else None,
            encryption_key=self.encryption_key.dumps(),
            signing_key=self.signing_key.dumps(),
            group_certificate_length=len(self.group_certificate.dumps()),
            group_certificate=self.group_certificate.dumps(),
        ))

    def dump(self, path: Union[Path, str]) -> None:
        if not isinstance(path, (Path, str)):
            raise ValueError(f"Expecting Path object or path string, got {path!r}")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.dumps())

    def get_name(self) -> str:
        name = f"{self.group_certificate.get_name()}_sl{self.group_certificate.get_security_level()}"
        return ''.join(char for char in name if (char.isalnum() or char in '_- ')).strip().lower().replace(" ", "_")

import base64
from enum import Enum
from uuid import UUID
from typing import Union

class Key:
    class KeyType(Enum):
        INVALID = 0x0000
        AES_128_CTR = 0x0001
        RC4_CIPHER = 0x0002
        AES_128_ECB = 0x0003
        COCKTAIL = 0x0004
        AES_128_CBC = 0x0005
        KEYEXCHANGE = 0x0006
        UNKNOWN = 0xffff

        @classmethod
        def _missing_(cls, value):
            return cls.UNKNOWN

    class CipherType(Enum):
        INVALID = 0x0000
        RSA_1024 = 0x0001
        CHAINED_LICENSE = 0x0002
        ECC_256 = 0x0003
        ECC_256_WITH_KZ = 0x0004
        TEE_TRANSIENT = 0x0005
        ECC_256_VIA_SYMMETRIC = 0x0006
        UNKNOWN = 0xffff

        @classmethod
        def _missing_(cls, value):
            return cls.UNKNOWN

    def __init__(
            self,
            key_id: UUID,
            key_type: int,
            cipher_type: int,
            key_length: int,
            key: bytes
    ):
        self.key_id = key_id
        self.key_type = self.KeyType(key_type)
        self.cipher_type = self.CipherType(cipher_type)
        self.key_length = key_length
        self.key = key

    @staticmethod
    def kid_to_uuid(kid: Union[str, bytes]) -> UUID:
        if isinstance(kid, str):
            kid = base64.b64decode(kid)
        if not kid:
            kid = b"\x00" * 16

        if kid.decode(errors="replace").isdigit():
            return UUID(int=int(kid.decode()))

        if len(kid) < 16:
            kid += b"\x00" * (16 - len(kid))

        return UUID(bytes=kid)

from ecpy.curves import Point, Curve

class XmlKey:

    def __init__(self):
        self.curve = Curve.get_curve("secp256r1")

        self._shared_point = ECCKey.generate()
        self.shared_key_x = self._shared_point.key.pointQ.x
        self.shared_key_y = self._shared_point.key.pointQ.y

        self._shared_key_x_bytes = Util.to_bytes(int(self.shared_key_x))
        self.aes_iv = self._shared_key_x_bytes[:16]
        self.aes_key = self._shared_key_x_bytes[16:]

    def get_point(self) -> Point:
        return Point(self.shared_key_x, self.shared_key_y, self.curve)
    
import time
from typing import Optional

from Crypto.Random import get_random_bytes

class Session:
    def __init__(self, number: int):
        self.number = number
        self.id = get_random_bytes(16)
        self.xml_key = XmlKey()
        self.signing_key: Optional[ECCKey] = None
        self.encryption_key: Optional[ECCKey] = None
        self.keys: list[Key] = []
        self.opened_at: float = time.time()

import base64
from enum import IntEnum
from typing import Union, Tuple
from uuid import UUID

from Crypto.Cipher import AES
from Crypto.Hash import CMAC
from Crypto.Util.strxor import strxor
from construct import Const, GreedyRange, Struct, Int32ub, Bytes, Int16ub, this, Switch, LazyBound, Array, Container

class XMRObjectTypes(IntEnum):
    INVALID = 0x0000
    OUTER_CONTAINER = 0x0001
    GLOBAL_POLICY_CONTAINER = 0x0002
    MINIMUM_ENVIRONMENT_OBJECT = 0x0003
    PLAYBACK_POLICY_CONTAINER = 0x0004
    OUTPUT_PROTECTION_OBJECT = 0x0005
    UPLINK_KID_OBJECT = 0x0006
    EXPLICIT_ANALOG_VIDEO_OUTPUT_PROTECTION_CONTAINER = 0x0007
    ANALOG_VIDEO_OUTPUT_CONFIGURATION_OBJECT = 0x0008
    KEY_MATERIAL_CONTAINER = 0x0009
    CONTENT_KEY_OBJECT = 0x000A
    SIGNATURE_OBJECT = 0x000B
    SERIAL_NUMBER_OBJECT = 0x000C
    SETTINGS_OBJECT = 0x000D
    COPY_POLICY_CONTAINER = 0x000E
    ALLOW_PLAYLISTBURN_POLICY_CONTAINER = 0x000F
    INCLUSION_LIST_OBJECT = 0x0010
    PRIORITY_OBJECT = 0x0011
    EXPIRATION_OBJECT = 0x0012
    ISSUEDATE_OBJECT = 0x0013
    EXPIRATION_AFTER_FIRSTUSE_OBJECT = 0x0014
    EXPIRATION_AFTER_FIRSTSTORE_OBJECT = 0x0015
    METERING_OBJECT = 0x0016
    PLAYCOUNT_OBJECT = 0x0017
    GRACE_PERIOD_OBJECT = 0x001A
    COPYCOUNT_OBJECT = 0x001B
    COPY_PROTECTION_OBJECT = 0x001C
    PLAYLISTBURN_COUNT_OBJECT = 0x001F
    REVOCATION_INFORMATION_VERSION_OBJECT = 0x0020
    RSA_DEVICE_KEY_OBJECT = 0x0021
    SOURCEID_OBJECT = 0x0022
    REVOCATION_CONTAINER = 0x0025
    RSA_LICENSE_GRANTER_KEY_OBJECT = 0x0026
    USERID_OBJECT = 0x0027
    RESTRICTED_SOURCEID_OBJECT = 0x0028
    DOMAIN_ID_OBJECT = 0x0029
    ECC_DEVICE_KEY_OBJECT = 0x002A
    GENERATION_NUMBER_OBJECT = 0x002B
    POLICY_METADATA_OBJECT = 0x002C
    OPTIMIZED_CONTENT_KEY_OBJECT = 0x002D
    EXPLICIT_DIGITAL_AUDIO_OUTPUT_PROTECTION_CONTAINER = 0x002E
    RINGTONE_POLICY_CONTAINER = 0x002F
    EXPIRATION_AFTER_FIRSTPLAY_OBJECT = 0x0030
    DIGITAL_AUDIO_OUTPUT_CONFIGURATION_OBJECT = 0x0031
    REVOCATION_INFORMATION_VERSION_2_OBJECT = 0x0032
    EMBEDDING_BEHAVIOR_OBJECT = 0x0033
    SECURITY_LEVEL = 0x0034
    COPY_TO_PC_CONTAINER = 0x0035
    PLAY_ENABLER_CONTAINER = 0x0036
    MOVE_ENABLER_OBJECT = 0x0037
    COPY_ENABLER_CONTAINER = 0x0038
    PLAY_ENABLER_OBJECT = 0x0039
    COPY_ENABLER_OBJECT = 0x003A
    UPLINK_KID_2_OBJECT = 0x003B
    COPY_POLICY_2_CONTAINER = 0x003C
    COPYCOUNT_2_OBJECT = 0x003D
    RINGTONE_ENABLER_OBJECT = 0x003E
    EXECUTE_POLICY_CONTAINER = 0x003F
    EXECUTE_POLICY_OBJECT = 0x0040
    READ_POLICY_CONTAINER = 0x0041
    EXTENSIBLE_POLICY_RESERVED_42 = 0x0042
    EXTENSIBLE_POLICY_RESERVED_43 = 0x0043
    EXTENSIBLE_POLICY_RESERVED_44 = 0x0044
    EXTENSIBLE_POLICY_RESERVED_45 = 0x0045
    EXTENSIBLE_POLICY_RESERVED_46 = 0x0046
    EXTENSIBLE_POLICY_RESERVED_47 = 0x0047
    EXTENSIBLE_POLICY_RESERVED_48 = 0x0048
    EXTENSIBLE_POLICY_RESERVED_49 = 0x0049
    EXTENSIBLE_POLICY_RESERVED_4A = 0x004A
    EXTENSIBLE_POLICY_RESERVED_4B = 0x004B
    EXTENSIBLE_POLICY_RESERVED_4C = 0x004C
    EXTENSIBLE_POLICY_RESERVED_4D = 0x004D
    EXTENSIBLE_POLICY_RESERVED_4E = 0x004E
    EXTENSIBLE_POLICY_RESERVED_4F = 0x004F
    REMOVAL_DATE_OBJECT = 0x0050
    AUX_KEY_OBJECT = 0x0051
    UPLINKX_OBJECT = 0x0052
    INVALID_RESERVED_53 = 0x0053
    APPLICATION_ID_LIST = 0x0054
    REAL_TIME_EXPIRATION = 0x0055
    ND_TX_AUTH_CONTAINER = 0x0056
    ND_TX_AUTH_OBJECT = 0x0057
    EXPLICIT_DIGITAL_VIDEO_PROTECTION = 0x0058
    DIGITAL_VIDEO_OPL = 0x0059
    SECURESTOP = 0x005A
    SECURESTOP2 = 0x005C
    OPTIMIZED_CONTENT_KEY2 = 0x005D
    COPY_UNKNOWN_OBJECT = 0xFFFD
    PLAYBACK_UNKNOWN_OBJECT = 0xFFFD
    GLOBAL_POLICY_UNKNOWN_OBJECT = 0xFFFD
    COPY_UNKNOWN_CONTAINER = 0xFFFE
    PLAYBACK_UNKNOWN_CONTAINER = 0xFFFE
    UNKNOWN_CONTAINERS = 0xFFFE

class _XMRLicenseStructs:
    PlayEnablerType = Struct(
        "player_enabler_type" / Bytes(16)
    )

    DomainRestrictionObject = Struct(
        "account_id" / Bytes(16),
        "revision" / Int32ub
    )

    IssueDateObject = Struct(
        "issue_date" / Int32ub
    )

    RevInfoVersionObject = Struct(
        "sequence" / Int32ub
    )

    SecurityLevelObject = Struct(
        "minimum_security_level" / Int16ub
    )

    EmbeddedLicenseSettingsObject = Struct(
        "indicator" / Int16ub
    )

    ECCKeyObject = Struct(
        "curve_type" / Int16ub,
        "key_length" / Int16ub,
        "key" / Bytes(this.key_length)
    )

    SignatureObject = Struct(
        "signature_type" / Int16ub,
        "signature_data_length" / Int16ub,
        "signature_data" / Bytes(this.signature_data_length)
    )

    ContentKeyObject = Struct(
        "key_id" / Bytes(16),
        "key_type" / Int16ub,
        "cipher_type" / Int16ub,
        "key_length" / Int16ub,
        "encrypted_key" / Bytes(this.key_length)
    )

    RightsSettingsObject = Struct(
        "rights" / Int16ub
    )

    OutputProtectionLevelRestrictionObject = Struct(
        "minimum_compressed_digital_video_opl" / Int16ub,
        "minimum_uncompressed_digital_video_opl" / Int16ub,
        "minimum_analog_video_opl" / Int16ub,
        "minimum_digital_compressed_audio_opl" / Int16ub,
        "minimum_digital_uncompressed_audio_opl" / Int16ub,
    )

    ExpirationRestrictionObject = Struct(
        "begin_date" / Int32ub,
        "end_date" / Int32ub
    )

    RemovalDateObject = Struct(
        "removal_date" / Int32ub
    )

    UplinkKIDObject = Struct(
        "uplink_kid" / Bytes(16),
        "chained_checksum_type" / Int16ub,
        "chained_checksum_length" / Int16ub,
        "chained_checksum" / Bytes(this.chained_checksum_length)
    )

    AnalogVideoOutputConfigurationRestriction = Struct(
        "video_output_protection_id" / Bytes(16),
        "binary_configuration_data" / Bytes(this._.length - 24)
    )

    DigitalVideoOutputRestrictionObject = Struct(
        "video_output_protection_id" / Bytes(16),
        "binary_configuration_data" / Bytes(this._.length - 24)
    )

    DigitalAudioOutputRestrictionObject = Struct(
        "audio_output_protection_id" / Bytes(16),
        "binary_configuration_data" / Bytes(this._.length - 24)
    )

    PolicyMetadataObject = Struct(
        "metadata_type" / Bytes(16),
        "policy_data" / Bytes(this._.length - 24)
    )

    SecureStopRestrictionObject = Struct(
        "metering_id" / Bytes(16)
    )

    MeteringRestrictionObject = Struct(
        "metering_id" / Bytes(16)
    )

    ExpirationAfterFirstPlayRestrictionObject = Struct(
        "seconds" / Int32ub
    )

    GracePeriodObject = Struct(
        "grace_period" / Int32ub
    )

    SourceIdObject = Struct(
        "source_id" / Int32ub
    )

    AuxiliaryKey = Struct(
        "location" / Int32ub,
        "key" / Bytes(16)
    )

    AuxiliaryKeysObject = Struct(
        "count" / Int16ub,
        "auxiliary_keys" / Array(this.count, AuxiliaryKey)
    )

    UplinkKeyObject3 = Struct(
        "uplink_key_id" / Bytes(16),
        "chained_length" / Int16ub,
        "checksum" / Bytes(this.chained_length),
        "count" / Int16ub,
        "entries" / Array(this.count, Int32ub)
    )

    CopyEnablerObject = Struct(
        "copy_enabler_type" / Bytes(16)
    )

    CopyCountRestrictionObject = Struct(
        "count" / Int32ub
    )

    MoveObject = Struct(
        "minimum_move_protection_level" / Int32ub
    )

    XmrObject = Struct(
        "flags" / Int16ub,
        "type" / Int16ub,
        "length" / Int32ub,
        "data" / Switch(
            lambda ctx: ctx.type,
            {
                XMRObjectTypes.OUTPUT_PROTECTION_OBJECT: OutputProtectionLevelRestrictionObject,
                XMRObjectTypes.ANALOG_VIDEO_OUTPUT_CONFIGURATION_OBJECT: AnalogVideoOutputConfigurationRestriction,
                XMRObjectTypes.CONTENT_KEY_OBJECT: ContentKeyObject,
                XMRObjectTypes.SIGNATURE_OBJECT: SignatureObject,
                XMRObjectTypes.SETTINGS_OBJECT: RightsSettingsObject,
                XMRObjectTypes.EXPIRATION_OBJECT: ExpirationRestrictionObject,
                XMRObjectTypes.ISSUEDATE_OBJECT: IssueDateObject,
                XMRObjectTypes.METERING_OBJECT: MeteringRestrictionObject,
                XMRObjectTypes.GRACE_PERIOD_OBJECT: GracePeriodObject,
                XMRObjectTypes.SOURCEID_OBJECT: SourceIdObject,
                XMRObjectTypes.ECC_DEVICE_KEY_OBJECT: ECCKeyObject,
                XMRObjectTypes.DOMAIN_ID_OBJECT: DomainRestrictionObject,
                XMRObjectTypes.POLICY_METADATA_OBJECT: PolicyMetadataObject,
                XMRObjectTypes.EXPIRATION_AFTER_FIRSTPLAY_OBJECT: ExpirationAfterFirstPlayRestrictionObject,
                XMRObjectTypes.DIGITAL_AUDIO_OUTPUT_CONFIGURATION_OBJECT: DigitalAudioOutputRestrictionObject,
                XMRObjectTypes.REVOCATION_INFORMATION_VERSION_2_OBJECT: RevInfoVersionObject,
                XMRObjectTypes.EMBEDDING_BEHAVIOR_OBJECT: EmbeddedLicenseSettingsObject,
                XMRObjectTypes.SECURITY_LEVEL: SecurityLevelObject,
                XMRObjectTypes.MOVE_ENABLER_OBJECT: MoveObject,
                XMRObjectTypes.PLAY_ENABLER_OBJECT: PlayEnablerType,
                XMRObjectTypes.COPY_ENABLER_OBJECT: CopyEnablerObject,
                XMRObjectTypes.UPLINK_KID_2_OBJECT: UplinkKIDObject,
                XMRObjectTypes.COPYCOUNT_2_OBJECT: CopyCountRestrictionObject,
                XMRObjectTypes.REMOVAL_DATE_OBJECT: RemovalDateObject,
                XMRObjectTypes.AUX_KEY_OBJECT: AuxiliaryKeysObject,
                XMRObjectTypes.UPLINKX_OBJECT: UplinkKeyObject3,
                XMRObjectTypes.DIGITAL_VIDEO_OPL: DigitalVideoOutputRestrictionObject,
                XMRObjectTypes.SECURESTOP: SecureStopRestrictionObject,
            },
            default=LazyBound(lambda ctx: _XMRLicenseStructs.XmrObject)
        )
    )

    XmrLicense = Struct(
        "signature" / Const(b"XMR\x00"),
        "xmr_version" / Int32ub,
        "rights_id" / Bytes(16),
        "containers" / GreedyRange(XmrObject)
    )

class XMRLicense(_XMRLicenseStructs):
    MagicConstantZero = bytes([
        0x7e, 0xe9, 0xed, 0x4a, 0xf7, 0x73, 0x22, 0x4f,
        0x00, 0xb8, 0xea, 0x7e, 0xfb, 0x02, 0x7c, 0xbb
    ])

    def __init__(
            self,
            parsed_license: Container,
            license_obj: _XMRLicenseStructs.XmrLicense = _XMRLicenseStructs.XmrLicense
    ):
        self.parsed = parsed_license
        self._license_obj = license_obj

    @classmethod
    def loads(cls, data: Union[str, bytes]) -> XMRLicense:
        if isinstance(data, str):
            data = base64.b64decode(data)
        if not isinstance(data, bytes):
            raise ValueError(f"Expecting Bytes or Base64 input, got {data!r}")

        licence = _XMRLicenseStructs.XmrLicense
        return cls(
            parsed_license=licence.parse(data),
            license_obj=licence
        )

    def dumps(self) -> bytes:
        return self._license_obj.build(self.parsed)

    def _locate(self, container: Container):
        if container.flags == 2 or container.flags == 3:
            return self._locate(container.data)
        else:
            return container

    def get_object(self, type_: int):
        for obj in self.parsed.containers:
            container = self._locate(obj)
            if container.type == type_:
                yield container.data

    def get_device_key_obj(self) -> Container:
        return next(self.get_object(XMRObjectTypes.ECC_DEVICE_KEY_OBJECT), None)

    def get_content_key_obj(self) -> Container:
        return next(self.get_object(XMRObjectTypes.CONTENT_KEY_OBJECT), None)

    def is_scalable(self) -> bool:
        return bool(next(self.get_object(XMRObjectTypes.AUX_KEY_OBJECT), None))

    def get_content_key(self, encryption_key: ECCKey) -> Key:
        ecc_key = self.get_device_key_obj()
        if ecc_key is None:
            raise InvalidXmrLicense("No ECC public key in license")

        if ecc_key.key != encryption_key.public_bytes():
            raise InvalidXmrLicense("Public encryption key does not match")

        content_key = self.get_content_key_obj()
        cipher_type = Key.CipherType(content_key.cipher_type)

        if cipher_type not in (Key.CipherType.ECC_256, Key.CipherType.ECC_256_WITH_KZ, Key.CipherType.ECC_256_VIA_SYMMETRIC):
            raise InvalidXmrLicense(f"Invalid cipher type {cipher_type}")

        via_symmetric = Key.CipherType(content_key.cipher_type) == Key.CipherType.ECC_256_VIA_SYMMETRIC

        decrypted = Crypto.ecc256_decrypt(encryption_key, content_key.encrypted_key)
        ci, ck = decrypted[:16], decrypted[16:]

        if self.is_scalable():
            ci, ck = decrypted[::2][:16], decrypted[1::2][:16]

            if via_symmetric:
                embedded_root_license = content_key.encrypted_key[:144]
                embedded_leaf_license = content_key.encrypted_key[144:]

                rgb_key = strxor(ck, self.MagicConstantZero)
                content_key_prime = AES.new(ck, AES.MODE_ECB).encrypt(rgb_key)

                aux_key = next(self.get_object(XMRObjectTypes.AUX_KEY_OBJECT))["auxiliary_keys"][0]["key"]

                uplink_x_key = AES.new(content_key_prime, AES.MODE_ECB).encrypt(aux_key)
                secondary_key = AES.new(ck, AES.MODE_ECB).encrypt(embedded_root_license[128:])

                embedded_leaf_license = AES.new(uplink_x_key, AES.MODE_ECB).encrypt(embedded_leaf_license)
                embedded_leaf_license = AES.new(secondary_key, AES.MODE_ECB).encrypt(embedded_leaf_license)

                ci, ck = embedded_leaf_license[:16], embedded_leaf_license[16:]

        if not self.check_signature(ci):
            raise InvalidXmrLicense("License integrity signature does not match")

        return Key(
            key_id=UUID(bytes_le=content_key.key_id),
            key_type=content_key.key_type,
            cipher_type=content_key.cipher_type,
            key_length=content_key.key_length,
            key=ck
        )

    def check_signature(self, integrity_key: bytes) -> bool:
        cmac = CMAC.new(integrity_key, ciphermod=AES)

        signature_data = next(self.get_object(XMRObjectTypes.SIGNATURE_OBJECT))
        cmac.update(self.dumps()[:-(signature_data.signature_data_length + 12)])

        return signature_data.signature_data == cmac.digest()
    
import base64
import copy
import hashlib
import xml.etree.ElementTree as ET
from typing import Union, Iterator

from Crypto.PublicKey import ECC

class License:
    def __init__(self, data: Union[str, bytes, ET.Element]):
        if not data:
            raise InvalidLicense("Data must not be empty")

        if isinstance(data, str):
            data = data.encode()

        if isinstance(data, bytes):
            self._root = ET.fromstring(data)
        elif isinstance(data, ET.Element):
            self._root = data
        else:
            raise InvalidLicense("Invalid data type")

        self._original_root = copy.deepcopy(self._root)
        Util.remove_namespaces(self._root)

        if self._root.tag != "AcquireLicenseResponse":
            raise InvalidLicense("License root must be AcquireLicenseResponse")

        self._Response = self._root.find("AcquireLicenseResult/Response")

        if self._Response is None:
            raise InvalidLicense("Response not found in license")

        self.rmsdk_version = self._Response.get("rmsdkVersion")

        self._LicenseResponse = self._Response.find("LicenseResponse")
        if self._Response is None:
            raise InvalidLicense("LicenseResponse not found in license")

        self.version = self._LicenseResponse.findtext("Version")

        self.licenses = list(self._load_licenses())
        self.rev_info = self._LicenseResponse.find("RevInfo")

        self.transaction_id = self._LicenseResponse.find("Acknowledgement/TransactionID")

        self.license_nonce = self._LicenseResponse.findtext("LicenseNonce")
        self.response_id = self._LicenseResponse.findtext("ResponseID")

        cert_chain_str = self._LicenseResponse.findtext("SigningCertificateChain")
        self.signing_certificate_chain = CertificateChain.loads(cert_chain_str) if cert_chain_str else None

    def _find_element_raw(self, name: str) -> ET.Element:
        return self._original_root.find(f".//{name}", {
            "": "http://www.w3.org/2000/09/xmldsig#",
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "proto": "http://schemas.microsoft.com/DRM/2007/03/protocols",
            "msg": "http://schemas.microsoft.com/DRM/2007/03/protocols/messages"
        })

    def _load_licenses(self) -> Iterator[XMRLicense]:
        Licenses = self._LicenseResponse.findall("Licenses/License")
        if Licenses is None:
            return iter([])

        for license_ in Licenses:
            yield XMRLicense.loads(license_.text)

    def is_verifiable(self):
        if self.signing_certificate_chain is None:
            return False

        signature = self._Response.find("Signature")

        if signature is None:
            return False
        if signature.findtext("SignedInfo/Reference/DigestValue") is None:
            return False
        if signature.findtext("SignatureValue") is None:
            return False

        return True

    def verify(self):
        if not self.is_verifiable():
            raise RuntimeError("Missing required information for license signature verification")

        ET.register_namespace("", "http://schemas.microsoft.com/DRM/2007/03/protocols")

        license_response_xml = ET.tostring(self._find_element_raw("proto:LicenseResponse"), short_empty_elements=False)
        response_hash = hashlib.sha256(license_response_xml).digest()

        Signature = self._Response.find("Signature")
        digest_value = base64.b64decode(Signature.findtext("SignedInfo/Reference/DigestValue"))

        if digest_value != response_hash:
            raise InvalidLicense("Digest mismatch in license")

        signing_leaf_cert = self.signing_certificate_chain.get(0)
        signing_key_bytes = signing_leaf_cert.get_key_by_usage(BCertKeyUsage.SIGN_RESPONSE)

        signing_key = ECC.construct(
            point_x=int.from_bytes(signing_key_bytes[:32], "big"),
            point_y=int.from_bytes(signing_key_bytes[32:], "big"),
            curve="P-256"
        )

        ET.register_namespace("", "http://www.w3.org/2000/09/xmldsig#")
        signed_info_xml = ET.tostring(self._find_element_raw("SignedInfo"), short_empty_elements=False)

        signature_value = base64.b64decode(Signature.findtext("SignatureValue"))

        if not Crypto.ecc256_verify(signing_key, signed_info_xml, signature_value):
            raise InvalidLicense("Signature mismatch in license")

        return True

import base64
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Union, Optional, Iterator
from uuid import UUID

from Crypto.PublicKey import ECC
from construct import Struct, Bytes, Switch, Int64ul, Int64ub, Int32ub, \
    Int16ub, Int8ub, Array, this, Adapter, OneOf, If, Container, Select, GreedyBytes, String
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from ecpy import curve_defs
from ecpy.curve_defs import WEIERSTRASS
from ecpy.curves import Curve, Point
from ecpy.ecdsa import ECDSA
from ecpy.keys import ECPublicKey
import xml.etree.ElementTree as ET

class FileTime(Adapter):
    EPOCH_AS_FILETIME = 116444736000000000
    HUNDREDS_OF_NANOSECONDS = 10_000_000

    def _decode(self, obj, context):
        timestamp = (obj - self.EPOCH_AS_FILETIME) / self.HUNDREDS_OF_NANOSECONDS
        return datetime.fromtimestamp(timestamp, timezone.utc)

    def _encode(self, obj, context):
        return self.EPOCH_AS_FILETIME + int(obj.timestamp() * self.HUNDREDS_OF_NANOSECONDS)

class UUIDLe(Adapter):
    def _decode(self, obj, context):
        return UUID(bytes_le=obj)

    def _encode(self, obj, context):
        return obj.bytes_le

class _RevocationStructs:
    BRevInfoData = Struct(
        "magic" / OneOf(Int32ub, [0x524C5649, 0x524C5632]),
        "length" / Int32ub,
        "format_version" / Int8ub,
        "reserved" / Bytes(3),
        "sequence_number" / Int32ub,
        "issued_time" / Switch(lambda ctx: ctx.magic, {
            0x524C5649: FileTime(Int64ul),
            0x524C5632: FileTime(Int64ub),
        }),
        "record_count" / Int32ub,
        "records" / Array(this.record_count, Struct(
            "list_id" / UUIDLe(Bytes(16)),
            "version" / Int64ub
        ))
    )

    BRevInfoSigned = Struct(
        "data" / BRevInfoData,
        "signature_type" / Int8ub,
        "signature_size" / Switch(lambda ctx: ctx.signature_type, {
            1: 128,
            2: Int16ub
        }),
        "signature" / Bytes(this.signature_size),
        "certificate_chain_length" / If(this.signature_type == 1, Int32ub),
        "certificate_chain" / Select(CertificateChain.BCertChain, GreedyBytes)
    )

    BPrRLData = Struct(
        "id" / Bytes(16),
        "version" / Int32ub,
        "entry_count" / Int32ub,
        "revocation_entries" / Array(this.entry_count, Bytes(32)),
    )

    BPrRLSigned = Struct(
        "data" / BPrRLData,
        "signature_type" / Int8ub,
        "signature_length" / Int16ub,
        "signature" / Bytes(this.signature_length),
        "certificate_chain" / Select(CertificateChain.BCertChain, GreedyBytes)
    )

    WMDRMNETData = Struct(
        "version" / Int32ub,
        "entry_count" / Int32ub,
        "revocation_entries" / Array(this.entry_count, Bytes(20)),
        "certificate_chain_length" / Int32ub,
        "certificate_chain" / String(this.certificate_chain_length),
    )

    WMDRMNETSigned = Struct(
        "data" / WMDRMNETData,
        "signature_type" / Int8ub,
        "signature_length" / Int16ub,
        "signature" / Bytes(this.signature_length)
    )

class RevocationList(_RevocationStructs):

    class ListID:
        REV_INFO = UUID("CCDE5A55-A688-4405-A88B-D13F90D5BA3E")
        REV_INFO_V2 = UUID("52D1FF11-D388-4EDD-82B7-68EA4C20A16C")

        PLAYREADY_RUNTIME = UUID("4E9D8C8A-B652-45A7-9791-6925A6B4791F")
        PLAYREADY_APPLICATION = UUID("28082E80-C7A3-40B1-8256-19E5B6D89B27")

        WMDRMNET = UUID("CD75E604-543D-4A9C-9F09-FE6D24E8BF90")

        DEVICE_REVOCATION = UUID("3129E375-CEB0-47D5-9CCA-9DB74CFD4332")

        APP_REVOCATION = UUID("90A37313-0ECF-4CAA-A906-B188F6129300")

    SupportedListIds = [ListID.PLAYREADY_RUNTIME, ListID.PLAYREADY_APPLICATION, ListID.REV_INFO_V2, ListID.WMDRMNET]

    RevocationDataPubKeyAllowList = [
        bytes([
            0x3F, 0x3C, 0x09, 0x41, 0xB3, 0xE2, 0x45, 0xC4, 0xF0, 0x55, 0x32, 0xF1, 0x00, 0x40, 0xAA, 0x48,
            0xFD, 0x2A, 0xC8, 0x44, 0x23, 0x68, 0x2D, 0xBF, 0x45, 0xFE, 0x2A, 0x65, 0xFF, 0x4E, 0xFF, 0x3A,
            0x60, 0xC4, 0x2A, 0x71, 0x38, 0x61, 0xA3, 0xA7, 0xBC, 0x89, 0xB3, 0xE7, 0xB9, 0xA4, 0xF4, 0xAA,
            0xA2, 0x8B, 0xA8, 0xCE, 0xE6, 0x89, 0xBA, 0x8D, 0xF7, 0xB0, 0x1B, 0x6A, 0x79, 0xC7, 0xDC, 0x93,
        ])
    ]

    pubkeyWMDRMNDRevocation = bytes([
        0x17, 0xab, 0x8d, 0x43, 0xe6, 0x47, 0xef, 0xba, 0xbd, 0x23,
        0x44, 0x66, 0x9f, 0x64, 0x04, 0x84, 0xf8, 0xe7, 0x71, 0x39,
        0xc7, 0x07, 0x36, 0x25, 0x5d, 0xa6, 0x5f, 0xba, 0xb9, 0x00,
        0xef, 0x9c, 0x89, 0x6b, 0xf2, 0xc4, 0x81, 0x1d, 0xa2, 0x12
    ])

    CurrentRevListStorageName = "RevInfo_Current.xml"

    def __init__(self, parsed):
        self.parsed = parsed

    @staticmethod
    def _verify_crl_signatures(crl: Container, data_struct) -> None:
        if isinstance(crl.certificate_chain, bytes) and len(crl.certificate_chain) == 64:
            if crl.certificate_chain not in RevocationList.RevocationDataPubKeyAllowList:
                raise InvalidRevocationList("Unallowed revocation list signing public key")

            signing_pub_key = crl.certificate_chain
        else:
            signing_cert = CertificateChain(crl.certificate_chain)
            signing_cert.verify_chain(
                check_expiry=True,
                cert_type=BCertCertType.CRL_SIGNER
            )

            leaf_signing_cert = signing_cert.get(0)
            signing_pub_key = leaf_signing_cert.get_key_by_usage(BCertKeyUsage.SIGN_CRL)

        signing_key = ECC.construct(
            curve='P-256',
            point_x=int.from_bytes(signing_pub_key[:32]),
            point_y=int.from_bytes(signing_pub_key[32:])
        )

        sign_payload = data_struct.build(crl.data)

        if not Crypto.ecc256_verify(
            public_key=signing_key,
            data=sign_payload,
            signature=crl.signature
        ):
            raise InvalidRevocationList("Revocation List signature is not authentic")

    @staticmethod
    def _verify_wmdrmnet_wrap_signature(xml: str) -> bool:
        self = RevocationList

        msdrm_ecc1_params = {
            'name':       "msdrm-ecc1",
            'type':       WEIERSTRASS,
            'size':       160,
            'field':      0x89abcdef012345672718281831415926141424f7,
            'generator': (0x8723947fd6a3a1e53510c07dba38daf0109fa120,
                          0x445744911075522d8c3c5856d4ed7acda379936f),
            'order':      0x89abcdef012345672716b26eec14904428c2a675,
            'cofactor':   0x1,
            'a':          0x37a5abccd277bce87632ff3d4780c009ebe41497,
            'b':          0x0dd8dabf725e2f3228e85f1ad78fdedf9328239e,
        }

        curve_defs.curves.append(msdrm_ecc1_params)
        msdrm_ecc1 = Curve.get_curve("msdrm-ecc1")

        public_point = Point(
            x=int.from_bytes(self.pubkeyWMDRMNDRevocation[:20], "little"),
            y=int.from_bytes(self.pubkeyWMDRMNDRevocation[20:], "little"),
            curve=msdrm_ecc1,
            check=True
        )

        public_key = ECPublicKey(public_point)

        root = ET.fromstring(f"<root>{xml}</root>")
        signature_value_element = root.find("SIGNATURE/VALUE")

        if signature_value_element is None:
            raise InvalidRevocationList("No SIGNATURE VALUE found in WMDRMNET revocation wrap")

        signature_value = base64.b64decode(signature_value_element.text)
        if len(signature_value) != 40:
            raise InvalidRevocationList("Invalid WMDRMNET revocation wrap SIGNATURE length")

        r = int.from_bytes(signature_value[:20], "little")
        s = int.from_bytes(signature_value[20:], "little")

        if not r < msdrm_ecc1_params["order"] or not s < msdrm_ecc1_params["order"]:
            raise InvalidRevocationList("Invalid WMDRMNET revocation wrap SIGNATURE")

        data_element = root.find("DATA")
        if data_element is None:
            raise InvalidRevocationList("No DATA element found in WMDRMNET revocation wrap")

        data_bytes = ET.tostring(data_element, encoding="utf-8")
        data_digest = hashlib.sha1(data_bytes).digest()

        signer = ECDSA("ITUPLE")
        authentic = signer.verify(
            data_digest,
            (r, s),
            public_key
        )

        return True

    @staticmethod
    def _unwrap_wmdrmnet_list(xml: str) -> bytes:
        root = ET.fromstring(f"<root>{xml}</root>")
        data_template = root.findtext("DATA/TEMPLATE")

        if not data_template:
            raise InvalidRevocationList("No DATA/TEMPLATE found in WMDRMNET revocation wrap")

        return base64.b64decode(data_template)

    @staticmethod
    def _verify_prnd_certificate(data: str) -> None:
        root = ET.fromstring(data)

        ET.register_namespace("c", "http://schemas.microsoft.com/DRM/2004/02/cert")
        ET.register_namespace("", "http://www.w3.org/2000/09/xmldsig#")

        _ns = {"c": "http://schemas.microsoft.com/DRM/2004/02/cert"}

        for cert in root.findall("c:Certificate", _ns):
            data_elem = cert.find("c:Data", _ns)
            if data_elem is None:
                raise InvalidRevocationList("Missing Data")

            data_xml = ET.tostring(data_elem)

            Util.remove_namespaces(cert)

            digest_val = cert.findtext("Signature/SignedInfo/Reference/DigestValue")
            if not digest_val:
                raise InvalidRevocationList("Missing DigestValue")

            digest_calc = base64.b64encode(hashlib.sha1(data_xml).digest()).decode()
            if digest_val != digest_calc:
                raise InvalidRevocationList("Digest mismatch")

            rsa_key_value = cert.find("Signature/KeyInfo/KeyValue/RSAKeyValue")
            mod_b64 = rsa_key_value.findtext("Modulus")
            exp_b64 = rsa_key_value.findtext("Exponent")
            if not mod_b64 or not exp_b64:
                raise InvalidRevocationList("Missing Modulus/Exponent")

            modulus_int = int.from_bytes(base64.b64decode(mod_b64), "big")

            exp_raw = bytearray(base64.b64decode(exp_b64))
            exp_bytes = (b"\x00" + exp_raw[::-1])
            exponent_int = int.from_bytes(exp_bytes, "big")

            pub_key = rsa.RSAPublicNumbers(exponent_int, modulus_int).public_key(default_backend())

            sig_b64 = cert.findtext("Signature/SignatureValue")
            if not sig_b64:
                raise InvalidRevocationList("Missing SignatureValue")

            sig_bytes = base64.b64decode(sig_b64)

            pub_key.verify(
                signature=sig_bytes,
                data=data_xml,
                padding=padding.PSS(padding.MGF1(hashes.SHA1()), padding.PSS.MAX_LENGTH),
                algorithm=hashes.SHA1()
            )

    @staticmethod
    def _get_wmdrmnet_crl_keys(data: str) -> Iterator[rsa.RSAPublicKey]:
        root = ET.fromstring(data.encode())
        Util.remove_namespaces(root)

        for cert in root.findall('Certificate'):
            data_elem = cert.find("Data")
            if data_elem is None:
                continue

            key_usage_elem = data_elem.findtext('KeyUsage/SignCRL')
            if key_usage_elem != "1":
                continue

            rsa_elem = data_elem.find('PublicKey/KeyValue/RSAKeyValue')
            if rsa_elem is None:
                continue

            modulus_b64 = rsa_elem.findtext('Modulus')
            exponent_b64 = rsa_elem.findtext('Exponent')
            if not modulus_b64 or not exponent_b64:
                continue

            modulus = int.from_bytes(base64.b64decode(modulus_b64), 'big')
            exponent = int.from_bytes(base64.b64decode(exponent_b64), 'big')

            yield rsa.RSAPublicNumbers(exponent, modulus).public_key()

        return None

    @staticmethod
    def _parse_list(list_id: UUID, data: bytes):
        self = RevocationList

        if list_id in (self.ListID.REV_INFO, self.ListID.REV_INFO_V2):
            rev_info = self.BRevInfoSigned.parse(data)
            self._verify_crl_signatures(rev_info, self.BRevInfoData)

            return list_id, rev_info
        elif list_id in (self.ListID.PLAYREADY_RUNTIME, self.ListID.PLAYREADY_APPLICATION):
            pr_rl = self.BPrRLSigned.parse(data)
            self._verify_crl_signatures(pr_rl, self.BPrRLData)

            return list_id, pr_rl
        elif list_id == self.ListID.WMDRMNET:
            try:
                xml = data.decode("utf-16-le")
                if "<DATA>" in xml:
                    if not self._verify_wmdrmnet_wrap_signature(xml):
                        raise InvalidRevocationList("WMDRMNET wrap signature is not authentic")

                    wmdrmnet_data = self._unwrap_wmdrmnet_list(xml)
                else:
                    raise InvalidRevocationList("WMDRMNET revocation list cannot be valid UTF-16-LE and not be wrapped")
            except UnicodeDecodeError:
                wmdrmnet_data = base64.b64decode(data)

            wmdrmnet_parsed = self.WMDRMNETSigned.parse(wmdrmnet_data)
            certificate_chain = wmdrmnet_parsed.data.certificate_chain.decode()

            self._verify_prnd_certificate(certificate_chain)
            crl_pub_key = next(self._get_wmdrmnet_crl_keys(certificate_chain), None)

            crl_pub_key.verify(
                signature=wmdrmnet_parsed.signature,
                data=self.WMDRMNETData.build(wmdrmnet_parsed.data),
                padding=padding.PSS(padding.MGF1(hashes.SHA1()), padding.PSS.MAX_LENGTH),
                algorithm=hashes.SHA1()
            )

            return list_id, wmdrmnet_parsed

        return None

    @staticmethod
    def _remove_utf8_bom(data: bytes) -> bytes:

        if data[:3] == b"\xEF\xBB\xBF":
            return data[3:]
        return data

    @staticmethod
    def _verify_and_parse(revocation):
        list_id = revocation.find("ListID")

        if list_id is None or not list_id.text:
            raise InvalidRevocationList(f"<ListID> is either missing or empty")

        list_id_uuid = UUID(bytes_le=base64.b64decode(list_id.text))

        list_data = revocation.find("ListData")
        if list_data is None or not list_data.text:
            raise InvalidRevocationList(f"<ListData> is either missing or empty")

        return RevocationList._parse_list(list_id_uuid, base64.b64decode(list_data.text))

    @classmethod
    def loads(cls, data: Union[str, bytes, ET.Element]) -> RevocationList:
        if isinstance(data, str):
            data = data.encode()
        if isinstance(data, bytes):
            root = ET.fromstring(cls._remove_utf8_bom(data))
        else:
            root = data

        if root.tag != "RevInfo":
            raise InvalidRevocationList("Root element is not <RevInfo>")

        revocations = root.findall("Revocation")

        return cls(list(map(
            cls._verify_and_parse,
            revocations
        )))

    @classmethod
    def load(cls, path: Union[Path, str]) -> RevocationList:
        if not isinstance(path, (Path, str)):
            raise ValueError(f"Expecting Path object or path string, got {path!r}")
        with Path(path).open(mode="rb") as f:
            return cls.loads(f.read())

    @staticmethod
    def merge(root: ET.Element, root2: ET.Element) -> ET.Element:
        if root.tag != "RevInfo" or root2.tag != "RevInfo":
            raise InvalidRevocationList("Root element is not <RevInfo>")

        revocation = root.findall("Revocation")

        def _get_version(parsed):
            if parsed[0] in (RevocationList.ListID.REV_INFO, RevocationList.ListID.REV_INFO_V2):
                return parsed[1].data.sequence_number
            return parsed[1].data.version

        def find_in_revs(list_id: UUID):
            for rev in revocation:
                parsed_rev = RevocationList._verify_and_parse(rev)
                if parsed_rev[0] == list_id:
                    return rev, _get_version(parsed_rev)
            return None, None

        for revocation2 in root2.findall("Revocation"):
            parsed_rev2 = RevocationList._verify_and_parse(revocation2)

            rev_find, version = find_in_revs(parsed_rev2[0])
            if rev_find is None:
                root.append(revocation2)
            else:
                if _get_version(parsed_rev2) > version:
                    rev_find.find("ListData").text = revocation2.find("ListData").text

        return root

    def get_by_id(self, uuid: UUID) -> Optional[Container]:
        for rev_list in self.parsed:
            if rev_list[0] == uuid:
                return rev_list[1]

        return None

    def get_storage_file_name(self):
        rev_list = self.get_by_id(self.ListID.REV_INFO_V2)
        list_name = "RevInfo2"

        if rev_list is None:
            rev_list = self.get_by_id(self.ListID.REV_INFO)
            list_name = "RevInfo"

        if rev_list is None:
            raise InvalidRevocationList("No RevInfo available")

        list_version = rev_list.data.sequence_number
        list_date = rev_list.data.issued_time.strftime("%Y%m%d")

        return f"{list_name}v{list_version}_{list_date}.xml"

import html
import xml.etree.ElementTree as ET
from typing import Union, Optional

class SoapMessage:
    XML_DECLARATION = '<?xml version="1.0" encoding="utf-8"?>'

    _NS = {
        "soap": "http://schemas.xmlsoap.org/soap/envelope/",
        "envelope": "http://www.w3.org/2003/05/soap-envelope"
    }

    def __init__(self, root: ET.Element):
        self.root = root

    @classmethod
    def create(cls, message: ET.Element) -> SoapMessage:
        Envelope = ET.Element("soap:Envelope", {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
            "xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/"
        })

        Body = ET.SubElement(Envelope, "soap:Body")
        Body.append(message)

        return cls(Envelope)

    @classmethod
    def loads(cls, data: Union[str, bytes]) -> SoapMessage:
        if not data:
            raise InvalidSoapMessage("Data must not be empty")

        if isinstance(data, str):
            data = data.encode()

        parser = ET.XMLParser(encoding="utf-8")
        root = ET.fromstring(data, parser=parser)

        if not root.tag.endswith("Envelope"):
            raise InvalidSoapMessage("Soap Message root must be Envelope")

        return cls(root)

    def get_message(self) -> Optional[ET.Element]:
        Body = self.root.find("soap:Body", self._NS) or self.root.find("envelope:Body", self._NS)
        if Body is None:
            return None

        if len(list(Body)) == 0:
            return None

        return Body[0]

    @staticmethod
    def read_namespace(element) -> Optional[str]:
        if element.tag.startswith("{"):
            return element.tag.split("}")[0][1:]
        return None

    def raise_faults(self):
        fault = self.get_message()

        if not fault.tag.endswith("Fault"):
            return

        nsmap = {"soap": self.read_namespace(fault)}

        status_code = fault.findtext("detail/Exception/StatusCode")
        drm_result = DrmResult.from_code(status_code) if status_code is not None else None
        fault_text = fault.findtext("faultstring") or fault.findtext("soap:Reason/soap:Text", namespaces=nsmap)

        error_message = fault_text or getattr(drm_result, "message", "(No message)")
        exception_message = (f"[{drm_result.name}] " if drm_result else "") + error_message

        raise ServerException(exception_message)

    def dumps(self) -> str:
        xml_data = ET.tostring(
            self.root,
            short_empty_elements=False,
            encoding="utf-8"
        )

        return self.XML_DECLARATION + html.unescape(xml_data.decode())

import os
from pathlib import Path
from typing import Optional

from platformdirs import user_data_dir

class Storage:

    @staticmethod
    def _get_initialized_path() -> Path:
        storage_path = Path(user_data_dir("playready", "DevLARLEY"))
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path

    @staticmethod
    def write_file(file_name: str, data: bytes) -> bool:
        storage_path = Storage._get_initialized_path()
        storage_file = storage_path / file_name

        new_file = not storage_file.exists()

        storage_file.write_bytes(data)

        return new_file

    @staticmethod
    def read_file(file_name: str) -> Optional[bytes]:
        storage_path = Storage._get_initialized_path()
        storage_file = storage_path / file_name

        if not storage_file.exists():
            return None

        return storage_file.read_bytes()

import base64
import hashlib
import html
import time
import xml.etree.ElementTree as ET
from typing import Optional, List
from uuid import UUID

from Crypto.Random import get_random_bytes

class XmlBuilder:

    @staticmethod
    def _ClientInfo(parent: ET.Element, client_version: str) -> ET.Element:
        ClientInfo = ET.SubElement(parent, "CLIENTINFO")

        ClientVersion = ET.SubElement(ClientInfo, "CLIENTVERSION")
        ClientVersion.text = client_version

        return ClientVersion

    @staticmethod
    def _RevListInfo(parent: ET.Element, list_id: UUID, version: int) -> ET.Element:
        RevListInfo = ET.SubElement(parent, "RevListInfo")

        ListID = ET.SubElement(RevListInfo, "ListID")
        ListID.text = base64.b64encode(list_id.bytes_le).decode()

        Version = ET.SubElement(RevListInfo, "Version")
        Version.text = str(version)

        return RevListInfo

    @staticmethod
    def _RevocationLists(parent: ET.Element, rev_lists: List[UUID]) -> ET.Element:
        RevocationLists = ET.SubElement(parent, "RevocationLists")

        load_result = Storage.read_file(RevocationList.CurrentRevListStorageName)
        if load_result is None:
            for rev_list in rev_lists:
                XmlBuilder._RevListInfo(RevocationLists, rev_list, 0)

            return RevocationLists

        loaded_list = RevocationList.loads(load_result)

        for list_id, list_data in loaded_list.parsed:
            if list_id not in rev_lists:
                continue

            if list_id == RevocationList.ListID.REV_INFO_V2:
                version = list_data.data.sequence_number
            else:
                version = list_data.data.version

            XmlBuilder._RevListInfo(RevocationLists, list_id, version)

        return RevocationLists

    @staticmethod
    def _LicenseAcquisition(
            parent: ET.Element,
            wrmheader: str,
            protocol_version: int,
            wrmserver_data: bytes,
            client_data: bytes,
            client_info: Optional[str] = None,
            revocation_lists: Optional[List[UUID]] = None,
            custom_data: Optional[str] = None
    ) -> ET.Element:
        LA = ET.SubElement(parent, "LA", {
            "xmlns": "http://schemas.microsoft.com/DRM/2007/03/protocols",
            "Id": "SignedData",
            "xml:space": "preserve"
        })

        Version = ET.SubElement(LA, "Version")
        Version.text = str(protocol_version)

        ContentHeader = ET.SubElement(LA, "ContentHeader")
        ContentHeader.text = wrmheader

        if client_info is not None:
            XmlBuilder._ClientInfo(LA, client_info)

        if revocation_lists is not None:
            XmlBuilder._RevocationLists(LA, revocation_lists)

        if custom_data is not None:
            CustomData = ET.SubElement(LA, "CustomData")
            CustomData.text = html.escape(custom_data)

        LicenseNonce = ET.SubElement(LA, "LicenseNonce")
        LicenseNonce.text = base64.b64encode(get_random_bytes(16)).decode()

        ClientTime = ET.SubElement(LA, "ClientTime")
        ClientTime.text = str(int(time.time()))

        EncryptedData = ET.SubElement(LA, "EncryptedData", {
            "xmlns": "http://www.w3.org/2001/04/xmlenc#",
            "Type": "http://www.w3.org/2001/04/xmlenc#Element"
        })
        ET.SubElement(EncryptedData, "EncryptionMethod", {
            "Algorithm": "http://www.w3.org/2001/04/xmlenc#aes128-cbc"
        })

        KeyInfo = ET.SubElement(EncryptedData, "KeyInfo", {
            "xmlns": "http://www.w3.org/2000/09/xmldsig#"
        })

        EncryptedKey = ET.SubElement(KeyInfo, "EncryptedKey", {
            "xmlns": "http://www.w3.org/2001/04/xmlenc#"
        })
        ET.SubElement(EncryptedKey, "EncryptionMethod", {
            "Algorithm": "http://schemas.microsoft.com/DRM/2007/03/protocols#ecc256"
        })

        KeyInfoInner = ET.SubElement(EncryptedKey, "KeyInfo", {
            "xmlns": "http://www.w3.org/2000/09/xmldsig#"
        })
        KeyName = ET.SubElement(KeyInfoInner, "KeyName")
        KeyName.text = "WMRMServer"

        WRMServerData = ET.SubElement(ET.SubElement(EncryptedKey, "CipherData"), "CipherValue")
        WRMServerData.text = base64.b64encode(wrmserver_data).decode()

        ClientData = ET.SubElement(ET.SubElement(EncryptedData, "CipherData"), "CipherValue")
        ClientData.text = base64.b64encode(client_data).decode()

        return LA

    @staticmethod
    def _SignedInfo(parent: ET.Element, digest_value: bytes) -> ET.Element:
        SignedInfo = ET.SubElement(parent, "SignedInfo", {
            "xmlns": "http://www.w3.org/2000/09/xmldsig#"
        })
        ET.SubElement(SignedInfo, "CanonicalizationMethod", {
            "Algorithm": "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
        })
        ET.SubElement(SignedInfo, "SignatureMethod", {
            "Algorithm": "http://schemas.microsoft.com/DRM/2007/03/protocols#ecdsa-sha256"
        })

        Reference = ET.SubElement(SignedInfo, "Reference", {
            "URI": "#SignedData"
        })
        ET.SubElement(Reference, "DigestMethod", {
            "Algorithm": "http://schemas.microsoft.com/DRM/2007/03/protocols#sha256"
        })
        DigestValue = ET.SubElement(Reference, "DigestValue")
        DigestValue.text = base64.b64encode(digest_value).decode()

        return SignedInfo

    @staticmethod
    def AcquireLicenseMessage(
            wrmheader: str,
            protocol_version: int,
            wrmserver_data: bytes,
            client_data: bytes,
            signing_key: ECCKey,
            client_info: Optional[str] = None,
            revocation_lists: Optional[List[UUID]] = None,
            custom_data: Optional[str] = None
    ) -> ET.Element:
        AcquireLicense = ET.Element("AcquireLicense", {
            "xmlns": "http://schemas.microsoft.com/DRM/2007/03/protocols"
        })

        Challenge = ET.SubElement(ET.SubElement(AcquireLicense, "challenge"), "Challenge", {
            "xmlns": "http://schemas.microsoft.com/DRM/2007/03/protocols/messages"
        })

        LA = XmlBuilder._LicenseAcquisition(Challenge, wrmheader, protocol_version, wrmserver_data, client_data, client_info, revocation_lists, custom_data)

        Signature = ET.SubElement(Challenge, "Signature", {
            "xmlns": "http://www.w3.org/2000/09/xmldsig#"
        })

        la_xml = ET.tostring(
            LA,
            encoding="utf-8",
            short_empty_elements=False
        )
        unescaped_la_xml = html.unescape(la_xml.decode())
        la_digest = hashlib.sha256(unescaped_la_xml.encode()).digest()

        SignedInfo = XmlBuilder._SignedInfo(Signature, la_digest)

        signed_info_xml = ET.tostring(
            SignedInfo,
            encoding="utf-8",
            short_empty_elements=False
        )

        SignatureValue = ET.SubElement(Signature, "SignatureValue")
        SignatureValue.text = base64.b64encode(
            Crypto.ecc256_sign(signing_key, signed_info_xml)
        ).decode()

        ECCKeyValue = ET.SubElement(
            ET.SubElement(
                ET.SubElement(
                    Signature, "KeyInfo", {
                        "xmlns": "http://www.w3.org/2000/09/xmldsig#"
                    }
                ),
                "KeyValue"
            ), "ECCKeyValue"
        )

        PublicKey = ET.SubElement(ECCKeyValue, "PublicKey")
        PublicKey.text = base64.b64encode(signing_key.public_bytes()).decode()

        return AcquireLicense

    @staticmethod
    def ClientData(cert_chains: List[CertificateChain], ree_features: List[str]) -> str:
        Data = ET.Element("Data")
        CertificateChains = ET.SubElement(Data, "CertificateChains")

        for cert_chain in cert_chains:
            CertificateChainElement = ET.SubElement(CertificateChains, "CertificateChain")
            CertificateChainElement.text = f" {base64.b64encode(cert_chain.dumps()).decode()} "

        Features = ET.SubElement(Data, "Features")
        ET.SubElement(Features, "Feature", {"Name": "AESCBC"})

        REE = ET.SubElement(Features, "REE")
        for ree_feature in ree_features:
            ET.SubElement(REE, ree_feature)

        return ET.tostring(
            Data,
            encoding="utf-8",
            short_empty_elements=False
        ).decode()

import base64
import hashlib
from enum import Enum
from typing import List, Optional, Union
from uuid import UUID
import xml.etree.ElementTree as ET
from Crypto.Cipher import AES

class WRMHeader:

    class SignedKeyID:
        class AlgId(Enum):
            AESCTR = "AESCTR"
            AESCBC = "AESCBC"
            COCKTAIL = "COCKTAIL"
            UNKNOWN = "UNKNOWN"

            @classmethod
            def _missing_(cls, value):
                return cls.UNKNOWN

        def __init__(self, value: UUID, alg_id, checksum: Optional[bytes]):
            self.value = value
            self.alg_id = alg_id
            self.checksum = checksum

        @classmethod
        def load(cls, value: str, alg_id: str, checksum: Optional[str]):
            return cls(
                value=UUID(bytes_le=base64.b64decode(value)),
                alg_id=cls.AlgId(alg_id),
                checksum=base64.b64decode(checksum) if checksum else None
            )

        def __repr__(self):
            return f'SignedKeyID(value="{self.value}", alg_id={self.alg_id}, checksum={self.checksum})'

        def verify(self, content_key: bytes) -> bool:
            if self.value is None:
                raise InvalidChecksum("Key ID must not be empty")
            if self.checksum is None:
                raise InvalidChecksum("Checksum must not be empty")

            if self.alg_id == self.AlgId.AESCTR:
                cipher = AES.new(content_key, mode=AES.MODE_ECB)
                encrypted = cipher.encrypt(self.value.bytes_le)
                checksum = encrypted[:8]
            elif self.alg_id == self.AlgId.COCKTAIL:
                buffer = content_key.ljust(21, b"\x00")
                for _ in range(5):
                    buffer = hashlib.sha1(buffer).digest()
                checksum = buffer[:7]
            else:
                raise InvalidChecksum("Algorithm ID must be either \"AESCTR\" or \"COCKTAIL\"")

            return checksum == self.checksum

    class Version(Enum):
        VERSION_4_0_0_0 = "4.0.0.0"
        VERSION_4_1_0_0 = "4.1.0.0"
        VERSION_4_2_0_0 = "4.2.0.0"
        VERSION_4_3_0_0 = "4.3.0.0"
        UNKNOWN = "UNKNOWN"

        @classmethod
        def _missing_(cls, value):
            return cls.UNKNOWN

    def __init__(self, data: Union[str, bytes]):
        if not data:
            raise InvalidWrmHeader("Data must not be empty")

        if isinstance(data, str):
            try:
                data = base64.b64decode(data).decode()
            except Exception:
                data = data.encode("utf-16-le")

        self._raw_data = data
        self._root = ET.fromstring(data)
        Util.remove_namespaces(self._root)

        if self._root.tag != "WRMHEADER":
            raise InvalidWrmHeader("Data is not a valid WRMHEADER")

        self.version = self.Version(self._root.attrib.get("version"))

        self.key_ids: List[WRMHeader.SignedKeyID] = []
        self.la_url: Optional[str] = None
        self.lui_url: Optional[str] = None
        self.ds_id: Optional[str] = None
        self.custom_attributes: Optional[ET.Element] = None
        self.decryptor_setup: Optional[str] = None

        if self.version == self.Version.VERSION_4_0_0_0:
            self._load_v4_0_data(self._root)
        elif self.version == self.Version.VERSION_4_1_0_0:
            self._load_v4_1_data(self._root)
        elif self.version == self.Version.VERSION_4_2_0_0:
            self._load_v4_2_data(self._root)
        elif self.version == self.Version.VERSION_4_3_0_0:
            self._load_v4_3_data(self._root)

    def __repr__(self):
        attrs = ", \n          ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"

    @staticmethod
    def _attr(element, name):
        return element.attrib.get(name) if element is not None else None

    def _load_v4_0_data(self, parent: ET.Element):
        Data = parent.find("DATA")

        Kid = Data.findtext("KID")
        AlgId = Data.findtext("PROTECTINFO/ALGID")
        Checksum = Data.findtext("CHECKSUM")

        self.key_ids = [self.SignedKeyID.load(Kid, AlgId, Checksum)]

        self.la_url = Data.findtext("LA_URL")
        self.lui_url = Data.findtext("LUI_URL")
        self.ds_id = Data.findtext("DS_ID")

        self.custom_attributes = Data.find("CUSTOMATTRIBUTES")

    def _load_v4_1_data(self, parent: ET.Element):
        Data = parent.find("DATA")

        Kid = Data.find("PROTECTINFO/KID")
        if Kid is not None:
            Value = Kid.get("VALUE")
            AlgId = Kid.get("ALGID")
            Checksum = Kid.get("CHECKSUM")

            self.key_ids.append(self.SignedKeyID.load(Value, AlgId, Checksum))

        self.la_url = Data.findtext("LA_URL")
        self.lui_url = Data.findtext("LUI_URL")
        self.ds_id = Data.findtext("DS_ID")

        self.custom_attributes = Data.find("CUSTOMATTRIBUTES")
        self.decryptor_setup = Data.findtext("DECRYPTORSETUP")

    def _load_v4_2_data(self, parent: ET.Element):
        Data = parent.find("DATA")

        for kid in Data.findall("PROTECTINFO/KIDS/KID"):
            Value = kid.get("VALUE")
            AlgId = kid.get("ALGID")
            Checksum = kid.get("CHECKSUM")

            self.key_ids.append(self.SignedKeyID.load(Value, AlgId, Checksum))

        self.la_url = Data.findtext("LA_URL")
        self.lui_url = Data.findtext("LUI_URL")
        self.ds_id = Data.findtext("DS_ID")

        self.custom_attributes = Data.find("CUSTOMATTRIBUTES")
        self.decryptor_setup = Data.findtext("DECRYPTORSETUP")

    def _load_v4_3_data(self, parent: ET.Element):
        Data = parent.find("DATA")

        for kid in Data.findall("PROTECTINFO/KIDS/KID"):
            Value = kid.get("VALUE")
            AlgId = kid.get("ALGID")
            Checksum = kid.get("CHECKSUM")

            self.key_ids.append(self.SignedKeyID.load(Value, AlgId, Checksum))

        self.la_url = Data.findtext("LA_URL")
        self.lui_url = Data.findtext("LUI_URL")
        self.ds_id = Data.findtext("DS_ID")

        self.custom_attributes = Data.find("CUSTOMATTRIBUTES")
        self.decryptor_setup = Data.findtext("DECRYPTORSETUP")

    def dumps(self) -> str:
        return self._raw_data.decode("utf-16-le")

import base64
from typing import Union, List
from uuid import UUID

from construct import Struct, Int32ul, Int16ul, this, Bytes, Switch, Int8ub, Int24ub, Int32ub, Const, Container, \
    ConstructError, Rebuild, Default, If, PrefixedArray, Prefixed, GreedyBytes

class _PlayreadyPSSHStructs:
    PsshBox = Struct(
        "length" / Int32ub,
        "pssh" / Const(b"pssh"),
        "version" / Rebuild(Int8ub, lambda ctx: 1 if (hasattr(ctx, "key_ids") and ctx.key_ids) else 0),
        "flags" / Const(Int24ub, 0),
        "system_id" / Bytes(16),
        "key_ids" / Default(If(this.version == 1, PrefixedArray(Int32ub, Bytes(16))), None),
        "data" / Prefixed(Int32ub, GreedyBytes)
    )

    PlayreadyObject = Struct(
        "type" / Int16ul,
        "length" / Int16ul,
        "data" / Switch(
            this.type,
            {
                1: Bytes(this.length)
            },
            default=Bytes(this.length)
        )
    )

    PlayreadyHeader = Struct(
        "length" / Int32ul,
        "records" / PrefixedArray(Int16ul, PlayreadyObject)
    )

class PSSH(_PlayreadyPSSHStructs):
    SYSTEM_ID = UUID(hex="9a04f07998404286ab92e65be0885f95")

    def __init__(self, data: Union[str, bytes]):

        if not data:
            raise InvalidPssh("Data must not be empty")

        if isinstance(data, str):
            try:
                data = base64.b64decode(data)
            except Exception as e:
                raise InvalidPssh(f"Could not decode data as Base64, {e}")

        self.wrm_headers: List[WRMHeader]
        try:
            box = self.PsshBox.parse(data)
            if self._is_utf_16_le(box.data):
                self.wrm_headers = [WRMHeader(box.data)]
            else:
                prh = self.PlayreadyHeader.parse(box.data)
                self.wrm_headers = self._read_playready_objects(prh)
        except ConstructError:
            if int.from_bytes(data[:2], byteorder="little") > 3:
                try:
                    prh = self.PlayreadyHeader.parse(data)
                    self.wrm_headers = self._read_playready_objects(prh)
                except ConstructError:
                    raise InvalidPssh("Could not parse data as a PSSH Box nor a PlayReady Header")
            else:
                try:
                    pro = self.PlayreadyObject.parse(data)
                    self.wrm_headers = [WRMHeader(pro.data)]
                except ConstructError:
                    raise InvalidPssh("Could not parse data as a PSSH Box nor a PlayReady Object")

    @staticmethod
    def _is_utf_16_le(data: bytes) -> bool:
        if len(data) % 2 != 0:
            return False

        try:
            decoded = data.decode('utf-16-le')
        except UnicodeDecodeError:
            return False

        for char in decoded:
            if not (0x20 <= ord(char) <= 0x7E):
                return False

        return True

    @staticmethod
    def _read_playready_objects(header: Container) -> List[WRMHeader]:
        return list(map(
            lambda pro: WRMHeader(pro.data),
            filter(
                lambda pro: pro.type == 1,
                header.records
            )
        ))

import time
import xml.etree.ElementTree as ET
from typing import List, Union, Optional
from uuid import UUID

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from ecpy.curves import Point, Curve

class Cdm:
    MAX_NUM_OF_SESSIONS = 16
    SESSION_TIMEOUT = 30

    def __init__(
            self,
            security_level: int,
            certificate_chain: Optional[CertificateChain],
            encryption_key: Optional[ECCKey],
            signing_key: Optional[ECCKey],
            client_version: str = "10.0.16384.10011",
    ):
        self.security_level = security_level
        self.certificate_chain = certificate_chain
        self.encryption_key = encryption_key
        self.signing_key = signing_key
        self.client_version = client_version

        self._wmrm_key = Point(
            x=0xc8b6af16ee941aadaa5389b4af2c10e356be42af175ef3face93254e7b0b3d9b,
            y=0x982b27b5cb2341326e56aa857dbfd5c634ce2cf9ea74fca8f2af5957efeea562,
            curve=Curve.get_curve("secp256r1")
        )

        self.__sessions: dict[bytes, Session] = {}

    @classmethod
    def from_device(cls, device) -> Cdm:
        return cls(
            security_level=device.security_level,
            certificate_chain=device.group_certificate,
            encryption_key=device.encryption_key,
            signing_key=device.signing_key
        )

    def open(self) -> bytes:
        now = time.time()
        expired = [
            session_id for session_id, session in self.__sessions.items()
            if (now - session.opened_at) > self.SESSION_TIMEOUT
        ]
        for session_id in expired:
            del self.__sessions[session_id]

        if len(self.__sessions) > self.MAX_NUM_OF_SESSIONS:
            raise TooManySessions(f"Too many Sessions open ({self.MAX_NUM_OF_SESSIONS}).")

        session = Session(len(self.__sessions) + 1)
        self.__sessions[session.id] = session

        return session.id

    def close(self, session_id: bytes) -> None:
        session = self.__sessions.get(session_id)
        if not session:
            raise InvalidSession(f"Session identifier {session_id.hex()} is invalid.")
        del self.__sessions[session_id]

    def _get_cipher_data(self, session: Session) -> bytes:
        body = XmlBuilder.ClientData([self.certificate_chain], ["AESCBCS"])

        cipher = AES.new(
            key=session.xml_key.aes_key,
            mode=AES.MODE_CBC,
            iv=session.xml_key.aes_iv
        )

        ciphertext = cipher.encrypt(pad(
            body.encode(),
            AES.block_size
        ))

        return session.xml_key.aes_iv + ciphertext

    def get_license_challenge(
            self,
            session_id: bytes,
            wrm_header: Union[WRMHeader, str],
            rev_lists: Optional[List[UUID]] = None,
            custom_data: Optional[str] = None
    ) -> str:
        session = self.__sessions.get(session_id)
        if not session:
            raise InvalidSession(f"Session identifier {session_id.hex()} is invalid.")

        if isinstance(wrm_header, str):
            wrm_header = WRMHeader(wrm_header)
        if not isinstance(wrm_header, WRMHeader):
            raise ValueError(f"Expected wrm_header to be a {str} or {WRMHeader} not {wrm_header!r}")

        if rev_lists and not isinstance(rev_lists, list):
            raise ValueError(f"Expected rev_lists to be a {list} not {rev_lists!r}")

        match wrm_header.version:
            case WRMHeader.Version.VERSION_4_3_0_0:
                protocol_version = 5
            case WRMHeader.Version.VERSION_4_2_0_0:
                protocol_version = 4
            case _:
                protocol_version = 1

        session.signing_key = self.signing_key
        session.encryption_key = self.encryption_key

        acquire_license_message = XmlBuilder.AcquireLicenseMessage(
            wrmheader=wrm_header.dumps(),
            protocol_version=protocol_version,
            wrmserver_data=Crypto.ecc256_encrypt(self._wmrm_key, session.xml_key.get_point()),
            client_data=self._get_cipher_data(session),
            signing_key=self.signing_key,
            client_info=self.client_version,
            revocation_lists=rev_lists,
            custom_data=custom_data
        )
        soap_message = SoapMessage.create(acquire_license_message)

        return soap_message.dumps()

    def parse_license(self, session_id: bytes, soap_message: str) -> None:
        session = self.__sessions.get(session_id)
        if not session:
            raise InvalidSession(f"Session identifier {session_id.hex()} is invalid.")

        if not soap_message:
            raise InvalidXmrLicense("Cannot parse an empty licence message")
        if not isinstance(soap_message, str):
            raise InvalidXmrLicense(f"Expected licence message to be a {str}, not {soap_message!r}")
        if not session.encryption_key or not session.signing_key:
            raise InvalidSession("Cannot parse a license message without first making a license request")

        soap_message = SoapMessage.loads(soap_message)
        soap_message.raise_faults()

        licence = License(soap_message.get_message())
        if licence.is_verifiable():
            licence.verify()

        if licence.rev_info is not None:
            current_rev_info_file = Storage.read_file(RevocationList.CurrentRevListStorageName)

            if current_rev_info_file:
                new_rev_info = RevocationList.merge(ET.fromstring(current_rev_info_file), licence.rev_info)
            else:
                new_rev_info = licence.rev_info

            new_rev_info_xml = ET.tostring(
                new_rev_info,
                xml_declaration=True,
                encoding="utf-8"
            )
            Storage.write_file(RevocationList.CurrentRevListStorageName, new_rev_info_xml)
            Storage.write_file(RevocationList.loads(new_rev_info).get_storage_file_name(), new_rev_info_xml)

        for xmr_license in licence.licenses:
            session.keys.append(xmr_license.get_content_key(session.encryption_key))

    def get_keys(self, session_id: bytes) -> List[Key]:
        session = self.__sessions.get(session_id)
        if not session:
            raise InvalidSession(f"Session identifier {session_id.hex()} is invalid.")

        return session.keys

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import click
import requests
from Crypto.Random import get_random_bytes

__version__ = "0.8.4"

from typing import Union, Tuple
from Crypto.Hash import SHA256
from Crypto.Hash.SHA256 import SHA256Hash
from Crypto.PublicKey.ECC import EccKey
from Crypto.Signature import DSS
from ecpy.curves import Point, Curve

class Crypto:
    curve = Curve.get_curve("secp256r1")

    @staticmethod
    def ecc256_encrypt(public_key: Union[ECCKey, Point], plaintext: Union[Point, bytes]) -> bytes:
        if isinstance(public_key, ECCKey):
            public_key = public_key.get_point(Crypto.curve)
        if not isinstance(public_key, Point):
            raise ValueError(f"Expecting ECCKey or Point input, got {public_key!r}")

        if isinstance(plaintext, bytes):
            plaintext = Point(
                x=int.from_bytes(plaintext[:32], 'big'),
                y=int.from_bytes(plaintext[32:64], 'big'),
                curve=Crypto.curve
            )
        if not isinstance(plaintext, Point):
            raise ValueError(f"Expecting Point or Bytes input, got {plaintext!r}")

        point1, point2 = ElGamal.encrypt(plaintext, public_key)
        return b''.join([
            Util.to_bytes(point1.x),
            Util.to_bytes(point1.y),
            Util.to_bytes(point2.x),
            Util.to_bytes(point2.y)
        ])

    @staticmethod
    def ecc256_decrypt(private_key: ECCKey, ciphertext: Union[Tuple[Point, Point], bytes]) -> bytes:
        if isinstance(ciphertext, bytes):
            ciphertext = (
                Point(
                    x=int.from_bytes(ciphertext[:32], 'big'),
                    y=int.from_bytes(ciphertext[32:64], 'big'),
                    curve=Crypto.curve
                ),
                Point(
                    x=int.from_bytes(ciphertext[64:96], 'big'),
                    y=int.from_bytes(ciphertext[96:128], 'big'),
                    curve=Crypto.curve
                )
            )
        if not isinstance(ciphertext, Tuple):
            raise ValueError(f"Expecting Tuple[Point, Point] or Bytes input, got {ciphertext!r}")

        decrypted = ElGamal.decrypt(ciphertext, int(private_key.key.d))
        return Util.to_bytes(decrypted.x)

    @staticmethod
    def ecc256_sign(private_key: Union[ECCKey, EccKey], data: Union[SHA256Hash, bytes]) -> bytes:
        if isinstance(private_key, ECCKey):
            private_key = private_key.key
        if not isinstance(private_key, EccKey):
            raise ValueError(f"Expecting ECCKey or EccKey input, got {private_key!r}")

        if isinstance(data, bytes):
            data = SHA256.new(data)
        if not isinstance(data, SHA256Hash):
            raise ValueError(f"Expecting SHA256Hash or Bytes input, got {data!r}")

        signer = DSS.new(private_key, 'fips-186-3')
        return signer.sign(data)

    @staticmethod
    def ecc256_verify(public_key: Union[ECCKey, EccKey], data: Union[SHA256Hash, bytes], signature: bytes) -> bool:
        if isinstance(public_key, ECCKey):
            public_key = public_key.key
        if not isinstance(public_key, EccKey):
            raise ValueError(f"Expecting ECCKey or EccKey input, got {public_key!r}")

        if isinstance(data, bytes):
            data = SHA256.new(data)
        if not isinstance(data, SHA256Hash):
            raise ValueError(f"Expecting SHA256Hash or Bytes input, got {data!r}")

        verifier = DSS.new(public_key, 'fips-186-3')
        try:
            verifier.verify(data, signature)
            return True
        except ValueError:
            return False

class PlayReadyPsshKeyIdExtractor:
    @staticmethod
    def extract_key_ids(pssh: str) -> list[str]:
        key_ids: list[str] = []
        try:
            encoded_pssh = pssh.strip()
            encoded_pssh += "=" * ((4 - len(encoded_pssh) % 4) % 4)
            decoded_pssh = base64.b64decode(encoded_pssh)
            try:
                decoded_text: Any = decoded_pssh.decode("utf-16-le")
            except UnicodeDecodeError:
                decoded_text = decoded_pssh
            if isinstance(decoded_text, bytes):
                decoded_text = decoded_text.decode("utf-16-le", errors="ignore")
            start = decoded_text.find("<WRMHEADER")
            end = decoded_text.rfind("</WRMHEADER>") + len("</WRMHEADER>")
            if start < 0 or end <= len("</WRMHEADER>"):
                return key_ids
            xml_data = decoded_text[start:end]
            import xml.etree.ElementTree as ElementTree
            root = ElementTree.fromstring(xml_data)
            for element in root.iter():
                element.tag = element.tag.split("}", 1)[-1] if "}" in element.tag else element.tag
            data_node = root.find("DATA")
            discovered: list[str] = []
            if data_node is not None:
                custom_attributes = data_node.find("CUSTOMATTRIBUTES")
                if custom_attributes is not None:
                    kids_node = custom_attributes.find("KIDS")
                    if kids_node is not None:
                        for kid_node in kids_node.findall("KID"):
                            value = kid_node.get("VALUE")
                            if value:
                                discovered.append(value)
                protect_info = data_node.find("PROTECTINFO")
                if protect_info is not None:
                    kids_node = protect_info.find("KIDS")
                    if kids_node is not None:
                        for kid_node in kids_node.findall("KID"):
                            value = kid_node.get("VALUE")
                            if value:
                                discovered.append(value)
                    single_kid = protect_info.find("KID")
                    if single_kid is not None:
                        value = single_kid.get("VALUE")
                        if value:
                            discovered.append(value)
                if not discovered:
                    value = data_node.findtext("KID")
                    if value:
                        discovered.append(value)
            for value in discovered:
                try:
                    key_id = str(UUID(bytes_le=base64.b64decode(value))).replace("-", "")
                    if key_id not in key_ids:
                        key_ids.append(key_id)
                except Exception:
                    continue
        except Exception:
            return key_ids
        return key_ids

class PlayReadyHeaderBuilder:
    def __init__(self, key_hex: Optional[str] = None):
        self.key_hex = key_hex

    @staticmethod
    def encode_base64(data: bytes) -> str:
        return base64.b64encode(data).decode("ascii")

    @staticmethod
    def decode_base64(data: str) -> bytes:
        return base64.b64decode(data)

    @staticmethod
    def compute_checksum(key_id: bytes, key: bytes) -> bytes:
        from Crypto.Cipher import AES
        cipher = AES.new(key, AES.MODE_ECB)
        return cipher.encrypt(key_id)[:8]

    @staticmethod
    def wrap_header_xml(header_xml: str) -> bytes:
        header_utf16_le = header_xml.encode("utf-16-le")
        record = struct.pack("<HH", 1, len(header_utf16_le)) + header_utf16_le
        return struct.pack("<IH", len(record) + 6, 1) + record

    @staticmethod
    def convert_key_id_to_playready_bytes(key_id_hex: str) -> bytes:
        key_id = bytes.fromhex(key_id_hex)
        if len(key_id) != 16:
            raise ValueError("KID must be 16 bytes.")
        return key_id[3:4] + key_id[2:3] + key_id[1:2] + key_id[0:1] + key_id[5:6] + key_id[4:5] + key_id[7:8] + key_id[6:7] + key_id[8:]

    def compute_key_info(self, key_spec: tuple[str, Optional[str]]) -> tuple[str, Optional[str]]:
        key_id_hex, key_hex = key_spec
        playready_key_id = self.convert_key_id_to_playready_bytes(key_id_hex)
        checksum = None
        if key_hex:
            checksum = self.encode_base64(self.compute_checksum(playready_key_id, bytes.fromhex(key_hex)))
        return self.encode_base64(playready_key_id), checksum

    def compute_xml_key_id(self, key_spec: tuple[str, Optional[str]], algorithm_id: str, include_checksum: bool = False) -> str:
        xml_key_id, checksum = self.compute_key_info(key_spec)
        checksum_attribute = f' CHECKSUM="{checksum}"' if include_checksum and checksum else ""
        return f'<KID ALGID="{algorithm_id}"{checksum_attribute} VALUE="{xml_key_id}"></KID>'

    def build_header(self, version: str, header_spec: Optional[str], encryption_scheme: str, key_specs: list[tuple[str, Optional[str]]], include_checksum: bool = False) -> bytes:
        scheme_to_algorithm = {"cenc": "AESCTR", "cens": "AESCTR", "cbc1": "AESCBC", "cbcs": "AESCBC"}
        scheme = encryption_scheme.lower()
        if scheme not in scheme_to_algorithm:
            raise ValueError("Encryption scheme is not supported by PlayReady.")
        algorithm_id = scheme_to_algorithm[scheme]
        if algorithm_id == "AESCBC" and float(version) < 4.3:
            raise ValueError("AESCBC requires PlayReady 4.3 or higher.")
        if header_spec is None:
            header_spec = ""
        if header_spec.startswith("#"):
            header = self.decode_base64(header_spec[1:])
            if not header:
                raise ValueError("Invalid Base64 header data.")
            return header
        if header_spec.startswith("@") or (header_spec and Path(header_spec).exists()):
            header_path = Path(header_spec[1:] if header_spec.startswith("@") else header_spec)
            if not header_path.exists():
                raise FileNotFoundError(f"Header data file does not exist: {header_path}")
            header = header_path.read_bytes()
            header_xml = None
            if len(header) >= 2 and ((header[0] == 0xFF and header[1] == 0xFE) or (header[0] == 0xFE and header[1] == 0xFF)):
                header_xml = header.decode("utf-16")
            elif len(header) >= 2 and header[0] == ord("<") and header[1] != 0x00:
                header_xml = header.decode("utf-8")
            elif len(header) >= 2 and header[0] == ord("<") and header[1] == 0x00:
                header_xml = header.decode("utf-16-le")
            return self.wrap_header_xml(header_xml) if header_xml is not None else header
        fields: dict[str, str] = {}
        if header_spec:
            for pair in header_spec.split("#"):
                if not pair:
                    continue
                if ":" not in pair:
                    raise ValueError("Invalid header argument syntax.")
                name, value = pair.split(":", 1)
                fields[name] = value
        xml_protect_info = ""
        xml_extra = ""
        if version == "4.0":
            if len(key_specs) != 1:
                raise ValueError("PlayReady 4.0 only supports one key.")
            xml_key_id, _ = self.compute_key_info(key_specs[0])
            xml_protect_info = "<KEYLEN>16</KEYLEN><ALGID>AESCTR</ALGID>"
            xml_extra = f"<KID>{xml_key_id}</KID>"
        elif version == "4.1":
            if len(key_specs) != 1:
                raise ValueError("PlayReady 4.1 only supports one key.")
            xml_protect_info = self.compute_xml_key_id(key_specs[0], algorithm_id, include_checksum)
        else:
            xml_protect_info = "<KIDS>"
            for key_spec in key_specs:
                xml_protect_info += self.compute_xml_key_id(key_spec, algorithm_id, include_checksum)
            xml_protect_info += "</KIDS>"
        extra_xml = "".join(f"<{name}>{value}</{name}>" for name, value in fields.items())
        header_xml = (
            f'<WRMHEADER xmlns="http://schemas.microsoft.com/DRM/2007/03/PlayReadyHeader" version="{version}.0.0">'
            f"<DATA><PROTECTINFO>{xml_protect_info}</PROTECTINFO>{xml_extra}{extra_xml}</DATA></WRMHEADER>"
        )
        return self.wrap_header_xml(header_xml)

    @staticmethod
    def derive_content_key(seed: bytes, key_id: bytes, swap: bool = True) -> bytes:
        if len(seed) < 30:
            raise ValueError("Seed must be at least 30 bytes.")
        if len(key_id) != 16:
            raise ValueError("KID must be 16 bytes.")
        if swap:
            key_id = key_id[3:4] + key_id[2:3] + key_id[1:2] + key_id[0:1] + key_id[5:6] + key_id[4:5] + key_id[7:8] + key_id[6:7] + key_id[8:]
        seed = seed[:30]
        import hashlib
        sha_a = hashlib.sha256(seed + key_id).digest()
        sha_b = hashlib.sha256(seed + key_id + seed).digest()
        sha_c = hashlib.sha256(seed + key_id + seed + key_id).digest()
        return bytes(sha_a[index] ^ sha_a[index + 16] ^ sha_b[index] ^ sha_b[index + 16] ^ sha_c[index] ^ sha_c[index + 16] for index in range(16))

class InitializationPsshExtractor:
    PLAYREADY_SYSTEM_ID = "9a04f079-9840-4286-ab92-e65be0885f95"
    WIDEVINE_SYSTEM_ID = "edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"

    @staticmethod
    def read_file(path_value: Union[str, Path]) -> bytes:
        data = Path(path_value).read_bytes()
        if not data:
            raise ValueError("The file is empty.")
        return data

    @staticmethod
    def format_system_id(system_id: bytes) -> str:
        return "-".join([system_id[:4].hex(), system_id[4:6].hex(), system_id[6:8].hex(), system_id[8:10].hex(), system_id[10:].hex()]).lower()

    @classmethod
    def extract_pssh_boxes(cls, init_mp4: Union[str, Path]) -> list[tuple[str, bytes]]:
        data = cls.read_file(init_mp4)
        boxes: list[tuple[str, bytes]] = []
        index = 0
        while index < len(data):
            if data[index:index + 4] == b"pssh" and index >= 4:
                try:
                    box_size = struct.unpack(">I", data[index - 4:index])[0]
                    start = index - 4
                    end = start + box_size
                    if box_size >= 32 and end <= len(data):
                        box_data = data[start:end]
                        system_id = cls.format_system_id(box_data[12:28])
                        boxes.append((system_id, box_data))
                except Exception:
                    pass
            index += 1
        return boxes

    @classmethod
    def extract_widevine_pssh(cls, init_mp4: Union[str, Path]) -> Optional[str]:
        for system_id, box_data in cls.extract_pssh_boxes(init_mp4):
            if system_id == cls.WIDEVINE_SYSTEM_ID:
                return base64.b64encode(box_data).decode("utf-8")
        return None

    @classmethod
    def extract_playready_pssh(cls, init_mp4: Union[str, Path]) -> Optional[str]:
        for system_id, box_data in cls.extract_pssh_boxes(init_mp4):
            if system_id == cls.PLAYREADY_SYSTEM_ID:
                return base64.b64encode(box_data).decode("utf-8")
        return None

    @classmethod
    def extract_playready_header_from_init(cls, init_mp4: Union[str, Path]) -> Optional[str]:
        pssh = cls.extract_playready_pssh(init_mp4)
        if pssh:
            key_ids = PlayReadyPsshKeyIdExtractor.extract_key_ids(pssh)
            if key_ids:
                key_id = key_ids[0]
                header = PlayReadyHeaderBuilder(key_id).build_header("4.0", None, "cenc", [(key_id, key_id)])
                return base64.b64encode(header).decode("utf-8")
            return pssh
        widevine_pssh = cls.extract_widevine_pssh(init_mp4)
        if not widevine_pssh:
            return None
        raw = base64.b64decode(widevine_pssh)
        init_data = raw[32:]
        key_id = init_data.hex()[:32]
        if not key_id:
            return None
        header = PlayReadyHeaderBuilder(key_id).build_header("4.0", None, "cenc", [(key_id, key_id)])
        return base64.b64encode(header).decode("utf-8")

    @classmethod
    def extract_playready_pssh_with_mp4dump(cls, init_mp4: Union[str, Path], mp4dump_exe: Union[str, Path]) -> str:
        executable = Path(mp4dump_exe)
        if not executable.exists():
            raise EnvironmentError(f"mp4dump executable was not found: {executable}")
        import subprocess
        process = subprocess.run([str(executable), "--format", "json", "--verbosity", "3", str(init_mp4)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data = json.loads(process.stdout.decode("utf-8"))
        for item in data:
            if item.get("name") != "moov":
                continue
            for child in item.get("children", []):
                if child.get("system_id") == "[9a 04 f0 79 98 40 42 86 ab 92 e6 5b e0 88 5f 95]":
                    box_size = child["size"]
                    pssh_data = child["data"]
                    pssh_data_size = child["data_size"]
                    raw = bytes.fromhex(f'{box_size:08x}70737368000000009a04f07998404286ab92e65be0885f95{pssh_data_size:08x}{pssh_data.replace("[", "").replace("]", "").replace(" ", "")}')
                    return base64.b64encode(raw).decode("utf-8")
        return ""

def read_binary_input(value: Optional[str]) -> Optional[bytes]:
    if value is None:
        return None
    path = Path(value)
    if path.exists():
        return path.read_bytes()
    text = value.strip()
    try:
        return base64.b64decode(text)
    except Exception:
        try:
            return bytes.fromhex(text)
        except Exception:
            return text.encode("utf-8")

def parse_http_headers(values: Optional[list[str]]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in values or []:
        if ":" not in item:
            raise ValueError(f"Invalid header '{item}'. Expected format: 'Name: Value'.")
        name, value = item.split(":", 1)
        headers[name.strip()] = value.strip().strip('"')
    return headers

def get_device_display_name(device: Device) -> str:
    if hasattr(device, "get_name"):
        return device.get_name()
    if hasattr(device, "group_certificate") and hasattr(device.group_certificate, "get_name"):
        name = device.group_certificate.get_name()
        if name:
            return name
    return "unknown_device"

def get_device_security_level(device: Device) -> Any:
    if hasattr(device, "security_level"):
        return device.security_level
    if hasattr(device, "group_certificate") and hasattr(device.group_certificate, "get_security_level"):
        return device.group_certificate.get_security_level()
    return "unknown"

def resolve_prd_output_path(output: Optional[Union[str, Path]], device: Device, default_directory: Optional[Union[str, Path]] = None) -> Path:
    output_path = Path(output) if output else Path(default_directory or Path.cwd())
    if output_path.suffix:
        return output_path
    return output_path / f"{device.get_name()}.prd"

def load_playready_device_from_exported_files(
    certificate: Union[str, Path],
    key: Union[str, Path],
    encryption_key: Optional[Union[str, Path]] = None,
    signing_key: Optional[Union[str, Path]] = None
) -> Device:
    certificate_path = Path(certificate)
    key_path = Path(key)
    if not certificate_path.is_file():
        raise FileNotFoundError(f"Group certificate file does not exist: {certificate_path}")
    if not key_path.is_file():
        raise FileNotFoundError(f"Group key file does not exist: {key_path}")
    group_key = ECCKey.load(key_path)
    certificate_chain = CertificateChain.load(certificate_path)
    if certificate_chain.get(0).get_type() == BCertCertType.DEVICE:
        raise InvalidCertificateChain("The provided certificate chain already contains a DEVICE leaf certificate.")
    if certificate_chain.get(0).get_type() != BCertCertType.ISSUER:
        raise InvalidCertificateChain("The provided certificate chain must start with an ISSUER certificate.")
    if not certificate_chain.get(0).contains_public_key(group_key):
        raise InvalidCertificateChain("The group key does not match the provided certificate chain.")
    certificate_chain.verify_chain(check_expiry=True, cert_type=BCertCertType.ISSUER)
    selected_encryption_key = ECCKey.load(encryption_key) if encryption_key else ECCKey.generate()
    selected_signing_key = ECCKey.load(signing_key) if signing_key else ECCKey.generate()
    device_certificate = Certificate.new_leaf_cert(
        cert_id=get_random_bytes(16),
        security_level=certificate_chain.get_security_level(),
        client_id=get_random_bytes(16),
        signing_key=selected_signing_key,
        encryption_key=selected_encryption_key,
        group_key=group_key,
        parent=certificate_chain,
    )
    certificate_chain.prepend(device_certificate)
    certificate_chain.verify_chain(check_expiry=True, cert_type=BCertCertType.DEVICE)
    return Device(
        group_key=group_key.dumps(),
        encryption_key=selected_encryption_key.dumps(),
        signing_key=selected_signing_key.dumps(),
        group_certificate=certificate_chain.dumps(),
    )

def load_playready_device_from_directory(
    path: Union[str, Path],
    encryption_key: Optional[Union[str, Path]] = None,
    signing_key: Optional[Union[str, Path]] = None
) -> Device:
    directory = Path(path)
    certificate_path = directory / "bgroupcert.dat"
    key_path = directory / "zgpriv.dat"
    return load_playready_device_from_exported_files(
        certificate=certificate_path,
        key=key_path,
        encryption_key=encryption_key,
        signing_key=signing_key
    )

if not hasattr(Device, "from_files"):
    Device.from_files = staticmethod(load_playready_device_from_exported_files)

if not hasattr(Device, "from_directory"):
    Device.from_directory = staticmethod(load_playready_device_from_directory)

def command_info(args: argparse.Namespace) -> int:
    device = Device.load(args.input)
    print(f"Device Name: {get_device_display_name(device)}")
    print(f"Security Level: SL{get_device_security_level(device)}")
    print(f"Group Key: {'available' if getattr(device, 'group_key', None) else 'not available'}")
    if getattr(device, "group_key", None):
        print(f"Group Key Size: {len(device.group_key.dumps())} bytes")
    print(f"Encryption Key Size: {len(device.encryption_key.dumps())} bytes")
    print(f"Signing Key Size: {len(device.signing_key.dumps())} bytes")
    print(f"Group Certificate Size: {len(device.group_certificate.dumps())} bytes")
    print(f"Certificate Count: {device.group_certificate.count()}")
    return 0

def command_create_device(args: argparse.Namespace) -> int:
    if bool(args.key) == bool(args.protected_key):
        raise ValueError("You must provide exactly one of --key or --protected-key.")
    certificate_path = Path(args.certificate)
    if not certificate_path.is_file():
        raise FileNotFoundError(f"Group certificate file does not exist: {certificate_path}")
    if args.key:
        key_path = Path(args.key)
        if not key_path.is_file():
            raise FileNotFoundError(f"Group key file does not exist: {key_path}")
        group_key = ECCKey.load(key_path)
    else:
        protected_key_path = Path(args.protected_key)
        if not protected_key_path.is_file():
            raise FileNotFoundError(f"Protected group key file does not exist: {protected_key_path}")
        group_key = ECCKey.loads(unwrap_wrapped_key(protected_key_path.read_bytes()))
    certificate_chain = CertificateChain.load(certificate_path)
    if certificate_chain.get(0).get_type() == BCertCertType.DEVICE:
        raise InvalidCertificateChain("Device has already been provisioned.")
    if certificate_chain.get(0).get_type() != BCertCertType.ISSUER:
        raise InvalidCertificateChain("The leaf certificate must be an ISSUER certificate to create a DEVICE certificate.")
    if not certificate_chain.get(0).contains_public_key(group_key):
        raise InvalidCertificateChain("The group key does not match this certificate chain.")
    certificate_chain.verify_chain(check_expiry=True, cert_type=BCertCertType.ISSUER)
    encryption_key = ECCKey.load(args.encryption_key) if args.encryption_key else ECCKey.generate()
    signing_key = ECCKey.load(args.signing_key) if args.signing_key else ECCKey.generate()
    device_certificate = Certificate.new_leaf_cert(
        cert_id=get_random_bytes(16),
        security_level=certificate_chain.get_security_level(),
        client_id=get_random_bytes(16),
        signing_key=signing_key,
        encryption_key=encryption_key,
        group_key=group_key,
        parent=certificate_chain,
    )
    certificate_chain.prepend(device_certificate)
    certificate_chain.verify_chain(check_expiry=True, cert_type=BCertCertType.DEVICE)
    device = Device(
        group_key=group_key.dumps(),
        encryption_key=encryption_key.dumps(),
        signing_key=signing_key.dumps(),
        group_certificate=certificate_chain.dumps(),
    )
    output_path = resolve_prd_output_path(args.output, device)
    if output_path.exists() and not args.overwrite:
        print(f"A file already exists at the path '{output_path}', cannot overwrite.")
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(device.dumps())
    print(f"Created PlayReady Device file: {output_path.name}")
    print(f"Security Level: SL{device.security_level}")
    print(f"Group Key: {len(device.group_key.dumps())} bytes")
    print(f"Encryption Key: {len(device.encryption_key.dumps())} bytes")
    print(f"Signing Key: {len(device.signing_key.dumps())} bytes")
    print(f"Group Certificate: {len(device.group_certificate.dumps())} bytes")
    print(f"Saved to: {output_path.absolute()}")
    return 0

def command_build_device(args: argparse.Namespace) -> int:
    encryption_key_path = Path(args.encryption_key)
    signing_key_path = Path(args.signing_key)
    certificate_path = Path(args.certificate)
    if not encryption_key_path.is_file():
        raise FileNotFoundError(f"Encryption key file does not exist: {encryption_key_path}")
    if not signing_key_path.is_file():
        raise FileNotFoundError(f"Signing key file does not exist: {signing_key_path}")
    if not certificate_path.is_file():
        raise FileNotFoundError(f"Group certificate file does not exist: {certificate_path}")
    encryption_key = ECCKey.load(encryption_key_path)
    signing_key = ECCKey.load(signing_key_path)
    certificate_chain = CertificateChain.load(certificate_path)
    leaf_certificate = certificate_chain.get(0)
    if not leaf_certificate.contains_public_key(encryption_key.public_bytes()):
        raise InvalidCertificateChain("Leaf certificate does not contain the encryption public key.")
    if not leaf_certificate.contains_public_key(signing_key.public_bytes()):
        raise InvalidCertificateChain("Leaf certificate does not contain the signing public key.")
    certificate_chain.verify_chain(check_expiry=True, cert_type=BCertCertType.DEVICE)
    device = Device(
        group_key=None,
        encryption_key=encryption_key.dumps(),
        signing_key=signing_key.dumps(),
        group_certificate=certificate_chain.dumps(),
    )
    output_path = resolve_prd_output_path(args.output, device)
    if output_path.exists() and not args.overwrite:
        print(f"A file already exists at the path '{output_path}', cannot overwrite.")
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(device.dumps(version=2))
    print(f"Built PlayReady Device file: {output_path.name}")
    print(f"Security Level: SL{device.security_level}")
    print(f"Encryption Key: {len(device.encryption_key.dumps())} bytes")
    print(f"Signing Key: {len(device.signing_key.dumps())} bytes")
    print(f"Group Certificate: {len(device.group_certificate.dumps())} bytes")
    print(f"Saved to: {output_path.absolute()}")
    return 0

def command_export_device(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.is_file():
        raise FileNotFoundError(f"PRD file does not exist: {input_path}")
    output_root = Path(args.output) if args.output else Path.cwd()
    output_path = output_root / input_path.stem
    if output_path.exists() and any(output_path.iterdir()) and not args.overwrite:
        print("Output directory is not empty, cannot overwrite.")
        return 1
    output_path.mkdir(parents=True, exist_ok=True)
    device = Device.load(input_path)
    print(f"Exporting PlayReady Device file: {input_path.stem}")
    print(f"SL{device.security_level} {device.get_name()}")
    print(f"Saving to: {output_path}")
    if device.group_key:
        group_key_path = output_path / "zgpriv.dat"
        group_key_path.write_bytes(device.group_key.dumps(private_only=True))
        print("Exported Group Key as zgpriv.dat")
    else:
        print("Cannot export zgpriv.dat because version 2 devices do not store the group key.")
    export_chain = CertificateChain.loads(device.group_certificate.dumps())
    if export_chain.count() > 0 and export_chain.get(0).get_type() == BCertCertType.DEVICE:
        export_chain.remove(0)
    group_certificate_path = output_path / "bgroupcert.dat"
    group_certificate_path.write_bytes(export_chain.dumps())
    print("Exported Group Certificate to bgroupcert.dat")
    return 0

def command_reprovision_device(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.is_file():
        raise FileNotFoundError(f"PRD file does not exist: {input_path}")
    device = Device.load(input_path)
    if device.group_key is None:
        raise OutdatedDevice("This device does not support reprovisioning because it does not contain a group key.")
    if device.group_certificate.get(0).get_type() != BCertCertType.DEVICE:
        raise InvalidCertificateChain("Device is not provisioned.")
    device.group_certificate.remove(0)
    encryption_key = ECCKey.load(args.encryption_key) if args.encryption_key else ECCKey.generate()
    signing_key = ECCKey.load(args.signing_key) if args.signing_key else ECCKey.generate()
    device.encryption_key = encryption_key
    device.signing_key = signing_key
    new_certificate = Certificate.new_leaf_cert(
        cert_id=get_random_bytes(16),
        security_level=device.group_certificate.get_security_level(),
        client_id=get_random_bytes(16),
        signing_key=signing_key,
        encryption_key=encryption_key,
        group_key=device.group_key,
        parent=device.group_certificate,
    )
    device.group_certificate.prepend(new_certificate)
    device.group_certificate.verify_chain(check_expiry=True, cert_type=BCertCertType.DEVICE)
    output_path = Path(args.output) if args.output else input_path
    if output_path.exists() and output_path != input_path and not args.overwrite:
        print(f"A file already exists at the path '{output_path}', cannot overwrite.")
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(device.dumps())
    print(f"Reprovisioned PlayReady Device file: {output_path}")
    return 0

def command_inspect(args: argparse.Namespace) -> int:
    if bool(args.device) == bool(args.chain):
        raise ValueError("You must provide exactly one of --device or --chain.")
    if args.device:
        loaded_device = Device.load(args.device)
        certificate_chain = loaded_device.group_certificate
    else:
        certificate_chain = CertificateChain.load(args.chain)
    print("Certificate Chain Inspection")
    print(f"Version: {certificate_chain.parsed.version}")
    print(f"Certificate Count: {certificate_chain.parsed.certificate_count}")
    for index in range(certificate_chain.count()):
        certificate = certificate_chain.get(index)
        print(f"Certificate {index}")
        basic_info = certificate.get_attribute(BCertObjType.BASIC)
        if basic_info:
            print(f"  Certificate Type: {BCertCertType(basic_info.attribute.cert_type).name}")
            print(f"  Security Level: SL{basic_info.attribute.security_level}")
            print(f"  Expiration Date: {basic_info.attribute.expiration_date}")
            print(f"  Client ID: {basic_info.attribute.client_id.hex()}")
        certificate_name = certificate.get_name()
        if certificate_name:
            print(f"  Name: {certificate_name}")
        feature_info = certificate.get_attribute(BCertObjType.FEATURE)
        if feature_info and feature_info.attribute.feature_count > 0:
            features = [BCertFeatures(value).name for value in feature_info.attribute.features]
            print(f"  Features: {', '.join(features)}")
        key_info = certificate.get_attribute(BCertObjType.KEY)
        if key_info and key_info.attribute.key_count > 0:
            print("  Certificate Keys")
            for key_index, key in enumerate(key_info.attribute.cert_keys):
                print(f"    Key {key_index}")
                print(f"      Type: {BCertKeyType(key.type).name}")
                print(f"      Key Length: {key.length} bits")
                usages = [BCertKeyUsage(value).name for value in key.usages]
                if usages:
                    print(f"      Usages: {', '.join(usages)}")
    return 0

def command_license(args: argparse.Namespace) -> int:
    pssh = PSSH(args.pssh)
    if args.device:
        device = Device.load(args.device)
    elif args.device_dir:
        device = Device.from_directory(
            args.device_dir,
            encryption_key=args.encryption_key,
            signing_key=args.signing_key
        )
    elif args.certificate and args.key:
        device = Device.from_files(
            certificate=args.certificate,
            key=args.key,
            encryption_key=args.encryption_key,
            signing_key=args.signing_key
        )
    else:
        raise ValueError("Provide either --device, --device-dir, or both --certificate and --key.")
    cdm = Cdm.from_device(device) if hasattr(Cdm, "from_device") else Cdm(device)
    session_id = cdm.open()
    try:
        challenge = cdm.get_license_challenge(session_id, pssh)
        if args.challenge_output:
            Path(args.challenge_output).write_bytes(challenge)
            print(f"Wrote license challenge: {args.challenge_output}")
            return 0
        if not args.server and not args.license_response:
            print(base64.b64encode(challenge).decode())
            return 0
        if args.license_response:
            response_data = Path(args.license_response).read_bytes()
        else:
            import requests
            response = requests.post(args.server, data=challenge, headers=parse_http_headers(args.header))
            response.raise_for_status()
            response_data = response.content
        cdm.parse_license(session_id, response_data)
        for key in cdm.get_keys(session_id):
            if args.include_non_content or str(key.type).upper() == "CONTENT":
                print(f"[{key.type}] {key.kid.hex}:{key.key.hex()}")
        return 0
    finally:
        cdm.close(session_id)

def create_playready_header_from_kid(
    kid: str,
    key: Optional[str] = None,
    version: str = "4.0",
    encryption_scheme: str = "cenc",
    header_spec: Optional[str] = None,
    include_checksum: bool = False
) -> str:
    normalized_kid = kid.replace("-", "").strip()
    normalized_key = key.replace("-", "").strip() if key else normalized_kid
    header = PlayReadyHeaderBuilder(normalized_kid).build_header(
        version=version,
        header_spec=header_spec,
        encryption_scheme=encryption_scheme,
        key_specs=[(normalized_kid, normalized_key)],
        include_checksum=include_checksum
    )
    return base64.b64encode(header).decode("utf-8")

def load_playready_device(path: Union[str, Path]) -> Device:
    return Device.load(path)

def create_playready_cdm(device: Device) -> Cdm:
    return Cdm.from_device(device) if hasattr(Cdm, "from_device") else Cdm(device)

def command_pssh_to_kids(args: argparse.Namespace) -> int:
    key_ids = PlayReadyPsshKeyIdExtractor.extract_key_ids(args.pssh)
    if args.json:
        print(json.dumps({"kids": key_ids}, indent=2))
    else:
        for key_id in key_ids:
            print(key_id)
    return 0

def command_kid_to_playready_header(args: argparse.Namespace) -> int:
    key_specs: list[tuple[str, Optional[str]]] = []
    for value in args.key:
        if ":" in value:
            key_id_hex, key_hex = value.split(":", 1)
            key_specs.append((key_id_hex.strip().replace("-", ""), key_hex.strip()))
        else:
            key_specs.append((value.strip().replace("-", ""), None))
    header = PlayReadyHeaderBuilder().build_header(
        version=args.version,
        header_spec=args.header,
        encryption_scheme=args.scheme,
        key_specs=key_specs,
        include_checksum=args.include_checksum
    )
    output = base64.b64encode(header).decode("utf-8")
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote PlayReady header: {args.output}")
    else:
        print(output)
    return 0

def command_derive_playready_key(args: argparse.Namespace) -> int:
    seed = Path(args.seed).read_bytes() if Path(args.seed).exists() else bytes.fromhex(args.seed)
    key_id = bytes.fromhex(args.kid.replace("-", ""))
    key = PlayReadyHeaderBuilder.derive_content_key(seed, key_id, swap=not args.no_swap)
    print(key.hex())
    return 0

def command_extract_init_pssh(args: argparse.Namespace) -> int:
    if args.drm == "widevine":
        result = InitializationPsshExtractor.extract_widevine_pssh(args.input)
    elif args.drm == "playready":
        result = InitializationPsshExtractor.extract_playready_pssh(args.input)
    elif args.drm == "playready-header":
        result = InitializationPsshExtractor.extract_playready_header_from_init(args.input)
    else:
        raise ValueError(f"Unsupported DRM mode: {args.drm}")
    if not result:
        return 1
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Wrote extracted data: {args.output}")
    else:
        print(result)
    return 0

def command_extract_init_pssh_mp4dump(args: argparse.Namespace) -> int:
    result = InitializationPsshExtractor.extract_playready_pssh_with_mp4dump(args.input, args.mp4dump)
    if not result:
        return 1
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Wrote PlayReady PSSH: {args.output}")
    else:
        print(result)
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pypr", description="Single-file PlayReady command line utility.")
    subcommands = parser.add_subparsers(dest="cmd")

    parser_info = subcommands.add_parser("info", help="Display information about a PlayReady PRD device file.")
    parser_info.add_argument("input")
    parser_info.set_defaults(func=command_info)

    parser_create = subcommands.add_parser("create-device", help="Create a PlayReady PRD device file from an issuer certificate chain and group key.")
    parser_create.add_argument("-c", "--certificate", "--group-certificate", dest="certificate", required=True)
    parser_create.add_argument("-k", "--key", "--group-key", dest="key")
    parser_create.add_argument("-pk", "--protected-key", "--protected-group-key", dest="protected_key")
    parser_create.add_argument("-e", "--encryption-key", dest="encryption_key")
    parser_create.add_argument("-s", "--signing-key", dest="signing_key")
    parser_create.add_argument("-o", "--output")
    parser_create.add_argument("--overwrite", action="store_true")
    parser_create.set_defaults(func=command_create_device)

    parser_build = subcommands.add_parser("build-device", help="Build a version 2 PlayReady PRD device file from encryption and signing keys.")
    parser_build.add_argument("-e", "--encryption-key", dest="encryption_key", required=True)
    parser_build.add_argument("-s", "--signing-key", dest="signing_key", required=True)
    parser_build.add_argument("-c", "--certificate", "--group-certificate", dest="certificate", required=True)
    parser_build.add_argument("-o", "--output")
    parser_build.add_argument("--overwrite", action="store_true")
    parser_build.set_defaults(func=command_build_device)

    parser_reprovision = subcommands.add_parser("reprovision-device", help="Reprovision a PlayReady PRD device file.")
    parser_reprovision.add_argument("input")
    parser_reprovision.add_argument("-e", "--encryption-key", dest="encryption_key")
    parser_reprovision.add_argument("-s", "--signing-key", dest="signing_key")
    parser_reprovision.add_argument("-o", "--output")
    parser_reprovision.add_argument("--overwrite", action="store_true")
    parser_reprovision.set_defaults(func=command_reprovision_device)

    parser_inspect = subcommands.add_parser("inspect", help="Inspect a PlayReady device or certificate chain.")
    parser_inspect.add_argument("-d", "--device")
    parser_inspect.add_argument("-c", "--chain")
    parser_inspect.set_defaults(func=command_inspect)

    parser_export = subcommands.add_parser("export-device", help="Export a PlayReady PRD device file to zgpriv.dat and bgroupcert.dat.")
    parser_export.add_argument("input")
    parser_export.add_argument("-o", "--output")
    parser_export.add_argument("--overwrite", action="store_true")
    parser_export.set_defaults(func=command_export_device)

    parser_license = subcommands.add_parser("license", help="Create a PlayReady license challenge and optionally parse a response.")
    parser_license.add_argument("--pssh", required=True)
    parser_license.add_argument("-d", "--device")
    parser_license.add_argument("-D", "--device-dir")
    parser_license.add_argument("-c", "--certificate", "--group-certificate", dest="certificate")
    parser_license.add_argument("-k", "--key", "--group-key", dest="key")
    parser_license.add_argument("-e", "--encryption-key", dest="encryption_key")
    parser_license.add_argument("-s", "--signing-key", dest="signing_key")
    parser_license.add_argument("--server")
    parser_license.add_argument("-H", "--header", action="append", default=[])
    parser_license.add_argument("--challenge-output")
    parser_license.add_argument("--license-response")
    parser_license.add_argument("--include-non-content", action="store_true")
    parser_license.set_defaults(func=command_license)

    parser_kids = subcommands.add_parser("pssh-to-kids", help="Extract PlayReady KIDs from a PlayReady PSSH or header.")
    parser_kids.add_argument("pssh")
    parser_kids.add_argument("--json", action="store_true")
    parser_kids.set_defaults(func=command_pssh_to_kids)

    parser_header = subcommands.add_parser("kid-to-header", help="Build a Base64 PlayReady header from one or more KIDs.")
    parser_header.add_argument("-k", "--key", action="append", required=True, help="KID or KID:KEY. Can be repeated.")
    parser_header.add_argument("-v", "--version", default="4.0", choices=["4.0", "4.1", "4.2", "4.3"])
    parser_header.add_argument("-s", "--scheme", default="cenc", choices=["cenc", "cens", "cbc1", "cbcs"])
    parser_header.add_argument("--header")
    parser_header.add_argument("--include-checksum", action="store_true")
    parser_header.add_argument("-o", "--output")
    parser_header.set_defaults(func=command_kid_to_playready_header)

    parser_derive = subcommands.add_parser("derive-key", help="Derive a PlayReady content key from a seed and KID.")
    parser_derive.add_argument("--seed", required=True, help="Seed as a hex string or local file path.")
    parser_derive.add_argument("--kid", required=True)
    parser_derive.add_argument("--no-swap", action="store_true")
    parser_derive.set_defaults(func=command_derive_playready_key)

    parser_init = subcommands.add_parser("extract-init", help="Extract Widevine or PlayReady PSSH data from an initialization MP4.")
    parser_init.add_argument("input")
    parser_init.add_argument("--drm", default="playready", choices=["playready", "playready-header", "widevine"])
    parser_init.add_argument("-o", "--output")
    parser_init.set_defaults(func=command_extract_init_pssh)

    parser_mp4dump = subcommands.add_parser("extract-init-mp4dump", help="Extract PlayReady PSSH data from an initialization MP4 using mp4dump JSON output.")
    parser_mp4dump.add_argument("input")
    parser_mp4dump.add_argument("--mp4dump", required=True)
    parser_mp4dump.add_argument("-o", "--output")
    parser_mp4dump.set_defaults(func=command_extract_init_pssh_mp4dump)
    return parser

def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 0
    try:
        return int(args.func(args))
    except Exception as exc:
        print(str(exc))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())