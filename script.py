import zipfile
from quickread import range_file

url = "https://files.pythonhosted.org/packages/6a/23/08f7fd7afdd24184a400fcaebf921bd09b5b5235cbd62ffa02308a7d35d6/Django-3.0.1-py3-none-any.whl#sha256=b61295749be7e1c42467c55bcabdaee9fbe9496fdf9ed2e22cef44d9de2ff953"

rf = range_file.UrlRangeFile(url)
# Or wget the url below and
# rf = range_file.FSRangeFile("Django-3.0.1-py3-none-any.whl")
zf = zipfile.ZipFile(rf)

print(
    f"Read at opening: {rf.total_bytes_read() / 1024:.2f}kb"
    f" ({rf.bytes_read_ratio():.2%})"
)
# Read at opening: 315.34kb (4.35%)


contents = zf.open("Django-3.0.1.dist-info/METADATA").read().decode("utf-8")
print(f"File size: {len(contents) / 1024:.2f}kb")
# File size: 3.49kb

print(contents)
# ...
# Requires-Python: >=3.6
# Requires-Dist: pytz
# Requires-Dist: sqlparse (>=0.2.2)
# Requires-Dist: asgiref (~=3.2)
# Provides-Extra: argon2
# Requires-Dist: argon2-cffi (>=16.1.0) ; extra == 'argon2'
# Provides-Extra: bcrypt
# Requires-Dist: bcrypt ; extra == 'bcrypt'
# ...

print(
    f"After reading a single file: {rf.total_bytes_read() / 1024:.2f}kb"
    f" ({rf.bytes_read_ratio():.2%})"
)
# After reading a single file: 316.82kb (4.37%)
