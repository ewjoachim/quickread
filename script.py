import zipfile
from quickread import range_file

url = "https://files.pythonhosted.org/packages/6a/23/08f7fd7afdd24184a400fcaebf921bd09b5b5235cbd62ffa02308a7d35d6/Django-3.0.1-py3-none-any.whl#sha256=b61295749be7e1c42467c55bcabdaee9fbe9496fdf9ed2e22cef44d9de2ff953"

rf = range_file.UrlRangeFile(url)
# Or wget the url below and
# rf = range_file.FSRangeFile("Django-3.0.1-py3-none-any.whl")
zf = zipfile.ZipFile(rf)

print(f"Before: {rf.bytes_read_ratio():.2%}")

print(zf.open("Django-3.0.1.dist-info/METADATA").read().decode("utf-8"))

print(f"After: {rf.bytes_read_ratio():.2%}")
