import os
import subprocess
from common.config import VERSION, AUTHOR

app_name = "MyApp"

cmd = [
    "python", "-m", "nuitka",
    "--standalone",
    "--mingw64",
    "--enable-plugin=pyside6",
    # "--windows-disable-console",
    # "--windows-icon-from-ico=resource/images/logo.png",
    "--windows-icon-from-ico=resource/images/Gartoon-Team-Gartoon-Misc-Stock-New-Meeting-Hands.ico",
    "--output-dir=out",
    f"--windows-company-name={AUTHOR}",
    f"--windows-product-name={app_name}",
    f"--windows-product-version={VERSION}",
    "--follow-import-to=common",
    "--follow-import-to=components",
    "--follow-import-to=view",
    "entry.py"
]

os.system("python pack_resources.py")

print(" ".join(cmd))
subprocess.run(cmd, shell=False)
