import re
import sys
from urllib.parse import urljoin
from urllib.request import urlopen

locale = "enGB"
os = "Win"

# limelight
repair_server = "http://blizzard.vo.llnwd.net:80/o16/content/repair/wow/"

# akamai
dist_server = "http://dist.blizzard.com.edgesuite.net/wow-pod-retail/EU/15050.direct/"

# 4.3.4-15595 manifest filename
manifest_fn = "wow-15595-0C3502F50D17376754B9E9CB0109F4C5.mfil"

files = [
    ( "E1FC69A72E4E23A96DBD535B372974A8", "BackgroundDownloader.exe" ),
    ( "24433A51A32335A39D2AF8CB55C467D3", "Battle.net.dll" ),
    ( "82EF43D5F8D1B1C87C3505ECD241FFF6", "Blizzard Updater.exe" ),
    ( "4003E34416EBD25E4C115D49DC15E1A7", "dbghelp.dll" ),
    ( "57E72CAE12091DAFA29A8E4DB8B4F1D1", "divxdecoder.dll" ),
    ( "C7C7121E1DD819088403F514FEBD06BA", "Launcher.exe" ),
    ( "D34B3DA03C59F38A510EAA8CCC151EC7", "Microsoft.VC80.CRT.manifest" ),
    ( "1169436EE42F860C7DB37A4692B38F0E", "msvcr80.dll" ),
    ( "DE5A2E274F2D3F2B89A2E6EC9CD8FD2A", "Wow.exe" ),
    ( "78766BBBFC6F9E5DA5D930CB11F0A1E1", "WowError.exe" ),
    ( "E198F00FE056B24ED58B36E1C6A048F4", "Repair.exe" )
]


with urlopen(urljoin(dist_server, manifest_fn)) as handle:
    manifest = handle.read().decode()

locales = re.findall(r"serverpath=locale_(\w+)", manifest)
if locale not in locales:
    print(f"Locale '{locale}' not part of manifest. Valid locales are: {', '.join(locales)}.")
    sys.exit(1)

for csum, fn in files:
    url = urljoin(repair_server, f"{csum[0]}/{csum[1]}/{csum}")
    print(f"curl --create-dirs -C - -o \"{fn}\" \"{url}\"")

files = []
file = None
for line in manifest.split():
    if line.startswith("file="):
        if file is not None:
            files.append(file)
        file = dict(name=line.split('=')[1])
    else:
        if not file:
            continue
        key, value = line.split("=")
        file.update({key: value})
files.append(file)


def want_file(file):
    # os dependent files
    if os == "Win" and file['name'] == "Data/base-OSX.MPQ":
        return False
    elif os == "OSX" and file['name'] == "Data/base-Win.MPQ":
        return False

    # directories
    if 'path' not in file:
        if file['name'] in ("Data", f"Data/{locale}"):
            return True

    else:
        # only matching locale
        if file['path'].startswith("locale_"):
            if file['path'].split('_')[1] == locale:
                return True

        if file['path'] == "base":
            # localized data
            if file['name'].startswith(f"Data/{locale}"):
                return True

            # non localized basedir data
            if file['name'].split('/', maxsplit=1)[1].count('/') == 0:
                return True

    # default skip case
    return False

size = 0
for file in files:
    if want_file(file):
        size += int(file['size'])
print(f"# Expecting ~{round(size / 1024 / 1024)} MiB from manifest")

for file in filter(want_file, files):
    if 'path' not in file:
        print(f"mkdir -vp {file['name']}")
    else:
        url = urljoin(dist_server, file['name'])
        print(f"echo {file['name']}")
        print(f"curl --create-dirs -C - -o \"{file['name']}\" \"{url}\"")


