from quickread import wheel
import sys

default_url = "https://files.pythonhosted.org/packages/6a/23/08f7fd7afdd24184a400fcaebf921bd09b5b5235cbd62ffa02308a7d35d6/Django-3.0.1-py3-none-any.whl#sha256=b61295749be7e1c42467c55bcabdaee9fbe9496fdf9ed2e22cef44d9de2ff953"
url = sys.argv[1] if len(sys.argv) >= 2 else default_url

meta = wheel.get_wheel_meta(url)

print(meta.get_all("Requires-Dist"))
