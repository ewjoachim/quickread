import io
import typing

import ranges
import requests


class RangeFile(typing.BinaryIO):
    def __init__(self, min_bytes=100):
        self.min_bytes = min_bytes
        self.file = io.BytesIO()
        self.ranges = ranges.RangeSet()
        self._file_size = None

    @property
    def file_size(self):
        if self._file_size is None:
            self._file_size = self.get_file_size()
        return self._file_size

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __iter__(self):
        raise NotImplementedError

    def __next__(self):
        raise NotImplementedError

    def fileno(self):
        raise NotImplementedError

    def flush(self):
        raise NotImplementedError

    def isatty(self):
        raise NotImplementedError

    def readable(self):
        return True

    def writable(self):
        return False

    def readline(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError

    def writelines(self):
        raise NotImplementedError

    def truncate(self):
        raise NotImplementedError

    def readlines(self):
        raise NotImplementedError

    def seekable(self) -> bool:
        return True

    def close(self):
        raise NotImplementedError()

    def get_file_size(self) -> int:
        raise NotImplementedError

    def get_bytes(self, range: ranges.Range) -> bytes:
        raise NotImplementedError

    def tell(self):
        tell = self.file.tell()
        return tell

    def seek(self, n, whence=0):
        if whence == 1:
            n += self.tell()
        if whence == 2:
            n = self.file_size + n

        return self.file.seek(n)

    def read(self, n: int = None):
        start = self.tell()  # first read byte
        end = start + n if n else None

        kwargs = {"end": end} if end else {}
        read_range = ranges.Range(start=start, **kwargs)

        # If we already read the requested range
        if read_range & self.ranges == read_range:
            return self.file.read(n)

        if n:
            n_final = max(n, self.min_bytes)
            final_end = start + n_final
            final_range = ranges.Range(start=start, end=final_end)
        else:
            final_range = ranges.Range(start=start)

        value = self.get_bytes(final_range)
        if value:
            self.file.write(value)
            self.ranges.add(ranges.Range(start=start, end=start + len(value)))
            self.seek(start + min(n, len(value)) if n else len(value))

        if n:
            return value[:n]
        else:
            return value

    def total_bytes_read(self):
        return sum(r.length() for r in self.ranges.ranges())

    def bytes_read_ratio(self):
        return self.total_bytes_read() / self.file_size


class FSRangeFile(RangeFile):
    def __init__(self, path, **kwargs):
        self.fs_file = open(path, "rb")
        super().__init__(**kwargs)

    def get_bytes(self, range):
        if range.start != self.fs_file.tell():
            self.fs_file.seek(range.start)
        end = range.end if isinstance(range.end, int) else None
        if end:
            return self.fs_file.read(end - range.start)
        else:
            return self.fs_file.read()

    def get_file_size(self):
        old = self.fs_file.tell()
        self.fs_file.seek(0, 2)
        size = self.fs_file.tell()
        self.fs_file.seek(old)
        return size

    def close(self):
        self.fs_file.close()


class UrlRangeFile(RangeFile):
    def __init__(self, url, **kwargs):
        super().__init__(**kwargs)
        self.session = requests.session
        self.url = url

    def get_bytes(self, range):
        start = range.start
        end = (range.end - 1) if isinstance(range.end, int) else ""
        ranges_value = f"bytes={start}-{end}"
        response = requests.get(self.url, headers={"Range": ranges_value})
        self.raise_for_status(response)
        return response.content

    def get_file_size_from_response(self, response):
        return int(response.headers["Content-Length"])

    def get_file_size(self):
        response = requests.head(self.url)
        self.raise_for_status(response)
        return self.get_file_size_from_response(response)

    def close(self):
        self.session.close()

    def raise_for_status(self, response):
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise Exception(
                f"HTTP {response.status_code}\n{response.headers}\n\n{response.text}"
            ) from exc
