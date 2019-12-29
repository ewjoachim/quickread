import email
import pathlib
import struct
import urllib.parse
import zlib
from zipfile import (
    _CD_COMPRESSED_SIZE,
    _CD_FILENAME_LENGTH,
    _CD_LOCAL_HEADER_OFFSET,
    _CD_SIGNATURE,
    _FH_EXTRA_FIELD_LENGTH,
    _FH_FILENAME_LENGTH,
    _FH_SIGNATURE,
    _FH_UNCOMPRESSED_SIZE,
    BadZipFile,
)
from zipfile import sizeCentralDir as size_central_dir
from zipfile import sizeFileHeader as size_file_header
from zipfile import stringCentralDir as string_central_dir
from zipfile import stringFileHeader as string_file_header
from zipfile import structCentralDir as struct_central_dir
from zipfile import structFileHeader as struct_file_header

import requests


class NoFileFound(Exception):
    pass


class WrongFile(Exception):
    pass


class WheelNotFound(Exception):
    pass


def get_wheel_meta(url):
    # Metadata file is named "{dist_name}.dist-info/METADATA"
    # We'll both be looking for that name and counting
    dist_name = get_dist_name(url)
    wheel_filename = f"{dist_name}.dist-info/METADATA"

    # The file we're looking for is the 5th last file
    reverse_file_order = 5

    # If dist_name was "", the beginning of the METADATA record would be 355 bytes
    # before the end of the file
    offset_without_dist_name = 355

    record_offset = offset_without_dist_name + reverse_file_order * len(dist_name)

    last_bytes = get_last_bytes(url, length=record_offset)

    wheel_offset, wheel_size = get_wheel_offset(
        last_bytes, expected_filename=wheel_filename
    )

    record_size = wheel_size + 30 + len(wheel_filename)
    wheel_record_bytes = get_bytes_range(url, wheel_offset, wheel_offset + record_size)
    meta_bytes = read_file(wheel_record_bytes, expected_filename=wheel_filename)

    return email.message_from_bytes(meta_bytes)


def get_wheel_offset(zip_bytes, expected_filename):
    bytes_record = zip_bytes[:size_central_dir]
    record = struct.unpack(struct_central_dir, bytes_record)

    if record[_CD_SIGNATURE] != string_central_dir:
        raise BadZipFile("Bad magic number for central dir record")

    filename = zip_bytes[
        size_central_dir : size_central_dir + record[_CD_FILENAME_LENGTH]
    ].decode("utf_8")

    if filename != expected_filename:
        raise WrongFile(f"File is {filename}, not {expected_filename}")

    return record[_CD_LOCAL_HEADER_OFFSET], record[_CD_COMPRESSED_SIZE]


def get_dist_name(url):
    components = urllib.parse.urlparse(url)
    filename = pathlib.Path(components.path).name
    package_name, version, _ = filename.split("-", 2)
    return f"{package_name}-{version}"


def get_bytes(url, range):
    response = requests.get(url, headers={"Range": f"bytes={range}"})
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise Exception(
            f"HTTP {response.status_code}\n{response.headers}\n\n{response.text}"
        ) from exc

    return response.content


def get_last_bytes(url, length):
    print(f"Reading last {length} bytes")
    return get_bytes(url, f"-{length}")


def get_bytes_range(url, start, end):
    print(f"Reading {end - start} bytes ({start}>{end})")
    return get_bytes(url, f"{start}-{end - 1}")


def search_wheel(dist_name, zip_bytes):
    # We're not interested in results in the first bytes, because we'll be looking at
    # data before the match
    search_back = 26

    try:
        index = zip_bytes[search_back:].find(
            f"{dist_name}.dist-info/WHEEL".encode("utf-8")
        )
    except IndexError:
        raise WheelNotFound

    offset = struct.unpack("<L", zip_bytes[index - 4 : index])[0]
    breakpoint()
    file_length = struct.unpack("<L", zip_bytes[index - 26 : index - 22])[0]

    return offset, file_length


def read_file(zip_bytes, expected_filename):

    bytes_header = zip_bytes[:size_file_header]
    header = struct.unpack(struct_file_header, bytes_header)

    if header[_FH_SIGNATURE] != string_file_header:
        raise BadZipFile("Bad magic number for file header")

    start_filename = size_file_header
    end_filename = start_filename + header[_FH_FILENAME_LENGTH]
    filename = zip_bytes[start_filename:end_filename].decode("utf_8")
    if filename != expected_filename:
        raise WrongFile(f"File is {filename}, not {expected_filename}")

    assert header[_FH_EXTRA_FIELD_LENGTH] == 0
    start_bytes = end_filename
    end_bytes = start_bytes + +header[_FH_UNCOMPRESSED_SIZE]
    file_bytes = zip_bytes[start_bytes:end_bytes]

    data = zlib.decompress(file_bytes, wbits=-15)

    return data
