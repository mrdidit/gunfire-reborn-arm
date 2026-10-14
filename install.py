#!/usr/bin/env python3
"""Install the Gunfire ARM add-on as a separate Steam compatibility tool."""

import argparse
import ctypes
import hashlib
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request


TOOL_NAME = "GE-Proton11-7-arm64-Gunfire"
DISPLAY_NAME = "GE ARM - Gunfire"
ARCHIVE_NAME = "GE-Proton11-7-aarch64.tar.gz"
RELEASE_URL = "https://github.com/GloriousEggroll/proton-ge-custom/releases/download/GE-Proton11-7/"
ARCHIVE_SHA512 = "741cf70256f13b20d44952b590defd68b115814097f911c9ec053a64d33795267e2a982a5ce939407e8b649613eb3943bb2e2ebf4794d302ff96b83b61457cdd"
MAX_DOWNLOAD_BYTES = 2 * 1024 ** 3
DLL_PATH = Path("files/lib/wine/aarch64-windows/libarm64ecfex.dll")
PAYLOAD_SHA256 = "496494f69260e4758384b6ceecb8684e73f2b5b1659654a05bb4d83a3d6a3243"
BASE_HASHES = {
    "version": "5c8757707067c507943f116e4253640eb0883675afdb7909d6d0a355842e3f46",
    "files/lib/wine/aarch64-unix/ntdll.so": "6ba770ec0df52311b760a0866226a83c177f67227598f990942382cad42b4bc3",
    "files/lib/wine/aarch64-windows/ntdll.dll": "240ea49f0a94e4ef6b18f5cbc3c7a770b254a4cf1d063ff4bee1882a631a3c8f",
}


class InstallError(Exception):
    pass


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def exists(path):
    return os.path.lexists(path)


def check_directory_chain(base, relative):
    current = base
    for part in relative.parts:
        current = current / part
        if current.is_symlink() or not current.is_dir():
            raise InstallError(f"Expected a real directory: {current}")


def check_hash(path, expected):
    if not path.is_file():
        raise InstallError(f"Required file is missing: {path}")
    actual = digest(path)
    if actual != expected:
        raise InstallError(f"Unsupported or damaged file: {path}\n"
                           f"Expected SHA-256: {expected}\nActual SHA-256:   {actual}")


def validate_base(base):
    base = base.expanduser().resolve(strict=True)
    if base == Path(base.anchor) or not base.is_dir():
        raise InstallError("Select an existing GE-Proton11-7 ARM64 tool directory.")
    for relative, expected in BASE_HASHES.items():
        check_directory_chain(base, Path(relative).parent)
        check_hash(base / relative, expected)
    check_directory_chain(base, DLL_PATH.parent)
    if not (base / DLL_PATH).is_file():
        raise InstallError(f"The base tool is missing its runtime: {base / DLL_PATH}")
    for name in ("proton", "compatibilitytool.vdf"):
        if not (base / name).is_file():
            raise InstallError(f"The base tool is incomplete: missing {name}")
    if (base / "proton").is_symlink():
        raise InstallError("The base tool's proton launcher must be a regular file.")
    return base


def validate_package(package):
    package = package.resolve(strict=True)
    check_hash(package / "runtime/libarm64ecfex.dll", PAYLOAD_SHA256)
    licenses = package / "LICENSES"
    if licenses.is_symlink() or not licenses.is_dir() or not any(licenses.iterdir()):
        raise InstallError("The release package is missing its LICENSES directory.")
    for entry in licenses.rglob("*"):
        if entry.is_symlink() or not (entry.is_file() or entry.is_dir()):
            raise InstallError(f"Unexpected license entry: {entry}")
    return package


def destination(parent):
    parent = parent.expanduser().resolve()
    if parent == Path(parent.anchor) or (exists(parent) and not parent.is_dir()):
        raise InstallError(f"Invalid compatibility-tools directory: {parent}")
    target = parent / TOOL_NAME
    if exists(target):
        raise InstallError(f"Destination already exists; nothing was changed: {target}")
    return target


def validate(base, package, parent=None):
    base = base.expanduser().resolve(strict=True)
    target = destination(base.parent if parent is None else parent)
    if base == target:
        raise InstallError(f"Source and destination are the same: {target}")
    validate_base(base)
    validate_package(package)
    return base, target


def remove_staged_file(path):
    if not exists(path):
        return
    if path.is_dir() and not path.is_symlink():
        raise InstallError(f"Expected a file, found a directory: {path}")
    path.unlink()


def rename_without_replace(source, target):
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        rename = libc.renameat2
    except AttributeError as error:
        raise InstallError("This installer requires Linux renameat2 support.") from error
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                       ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(source), -100, os.fsencode(target), 1) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))


def prepare_stage(stage, package):
    validate_base(stage)
    for directory in (stage, stage / DLL_PATH.parent):
        directory.chmod((directory.stat().st_mode & 0o777) | 0o700)
    dll = stage / DLL_PATH
    remove_staged_file(dll)
    shutil.copyfile(package / "runtime/libarm64ecfex.dll", dll)
    dll.chmod(0o644)
    check_hash(dll, PAYLOAD_SHA256)

    metadata = stage / "compatibilitytool.vdf"
    remove_staged_file(metadata)
    metadata.write_text(
        '"compatibilitytools"\n{\n    "compat_tools"\n    {\n'
        f'        "{TOOL_NAME}"\n        {{\n'
        '            "install_path" "."\n'
        f'            "display_name" "{DISPLAY_NAME}"\n'
        '            "from_oslist" "windows"\n'
        '            "to_oslist" "linux"\n'
        '        }\n    }\n}\n', encoding="utf-8")
    remove_staged_file(stage / ".protonplus")
    license_target = stage / "gunfire-addon-licenses"
    if exists(license_target):
        raise InstallError(f"Unexpected existing add-on directory: {license_target}")
    shutil.copytree(package / "LICENSES", license_target)


def install(base, package, parent=None):
    base, target = validate(base, package, parent)
    if not shutil.which("cp"):
        raise InstallError("GNU cp is required to copy the existing compatibility tool.")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{TOOL_NAME}-", dir=target.parent) as temporary:
        stage = Path(temporary) / "tool"
        stage.mkdir()
        subprocess.run(["cp", "-a", "--reflink=auto", "--no-preserve=ownership",
                        "--", str(base) + "/.", str(stage)], check=True)
        prepare_stage(stage, package)
        rename_without_replace(stage, target)
    return target


def steam_compat_dir(steam_dir=None, compat_dir=None):
    if compat_dir is not None:
        return compat_dir.expanduser().resolve()
    candidates = ([steam_dir.expanduser()] if steam_dir is not None else
                  [Path.home() / ".local/share/Steam", Path.home() / ".steam/root"])
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve() / "compatibilitytools.d"
    raise InstallError("Steam's directory was not found. Specify --steam-dir PATH "
                       "or --compat-dir PATH.")


def find_base(parent):
    if not parent.is_dir():
        return None
    for candidate in sorted(parent.iterdir()):
        if candidate.name.startswith(".") or not candidate.is_dir():
            continue
        try:
            return validate_base(candidate)
        except (InstallError, OSError):
            continue
    return None


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Gunfire-ARM-Installer"})
    return urllib.request.urlopen(request, timeout=60)


def download_archive(directory):
    if re.fullmatch(r"[0-9a-f]{128}", ARCHIVE_SHA512) is None:
        raise InstallError("This installer is missing its pinned archive checksum.")
    checksum_name = ARCHIVE_NAME.removesuffix(".tar.gz") + ".sha512sum"
    with fetch(RELEASE_URL + checksum_name) as response:
        checksum_text = response.read(4097).decode("ascii").strip()
    match = re.fullmatch(r"([0-9a-fA-F]{128})[ \t]+\*?(?:\./)?" + re.escape(ARCHIVE_NAME), checksum_text)
    if match is None or match.group(1).lower() != ARCHIVE_SHA512:
        raise InstallError("The upstream checksum does not match this release's pinned archive.")
    archive_path = directory / ARCHIVE_NAME
    print(f"Downloading official {ARCHIVE_NAME}...")
    value, total = hashlib.sha512(), 0
    with fetch(RELEASE_URL + ARCHIVE_NAME) as response, archive_path.open("xb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD_BYTES:
                raise InstallError("The archive exceeds the expected download size limit.")
            output.write(chunk)
            value.update(chunk)
    if value.hexdigest() != ARCHIVE_SHA512:
        raise InstallError("The downloaded archive failed SHA-512 verification.")
    return archive_path


def archive_parts(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise InstallError(f"Unsafe archive path: {name}")
    return path.parts


def extract_archive(archive_path, directory):
    with tarfile.open(archive_path, "r:gz") as archive:
        entries = {}
        for member in archive.getmembers():
            parts = archive_parts(member.name)
            if parts in entries:
                raise InstallError(f"Duplicate archive path: {member.name}")
            if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                raise InstallError(f"Unsupported archive entry: {member.name}")
            entries[parts] = member
        roots = {parts[0] for parts in entries}
        if len(roots) != 1:
            raise InstallError("The archive must contain one tool directory.")
        root_name = next(iter(roots))
        if (root_name,) in entries and not entries[(root_name,)].isdir():
            raise InstallError("The archive root must be a directory.")
        for parts, member in entries.items():
            for length in range(1, len(parts)):
                ancestor = entries.get(parts[:length])
                if ancestor is not None and not ancestor.isdir():
                    raise InstallError(f"Archive entry has a non-directory parent: {member.name}")
            if (member.issym() or member.islnk()) and PurePosixPath(member.linkname).is_absolute():
                raise InstallError(f"Absolute archive link: {member.name}")

        directory.mkdir()
        for parts, member in entries.items():
            output = directory.joinpath(*parts)
            output.parent.mkdir(parents=True, exist_ok=True)
            if member.isdir():
                output.mkdir(exist_ok=True)
            elif member.isfile():
                with archive.extractfile(member) as source, output.open("xb") as dest:
                    shutil.copyfileobj(source, dest, 1024 * 1024)
                output.chmod(member.mode & 0o777)
        for parts, member in entries.items():
            if not member.islnk():
                continue
            seen = {parts}
            target_parts = archive_parts(member.linkname)
            while True:
                target = entries.get(target_parts)
                if target_parts in seen or target is None or not (target.isfile() or target.islnk()):
                    raise InstallError(f"Unsafe archive hard link: {member.name}")
                seen.add(target_parts)
                if target.isfile():
                    break
                target_parts = archive_parts(target.linkname)
            os.link(directory.joinpath(*target_parts), directory.joinpath(*parts))
        for parts, member in entries.items():
            if member.issym():
                directory.joinpath(*parts).symlink_to(member.linkname)
        root = directory / root_name
        for parts, member in entries.items():
            if member.issym():
                link = directory.joinpath(*parts)
                try:
                    link.resolve().relative_to(root)
                except (ValueError, RuntimeError) as error:
                    raise InstallError(f"Archive link escapes the tool or forms a cycle: {member.name}") from error
        return root


def install_download(package, parent):
    validate_package(package)
    target = destination(parent)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{TOOL_NAME}-", dir=target.parent) as temporary:
        temporary = Path(temporary)
        archive = download_archive(temporary)
        print("Archive verified. Extracting the compatibility tool...")
        stage = extract_archive(archive, temporary / "unpacked")
        archive.unlink()
        prepare_stage(stage, package)
        rename_without_replace(stage, target)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", nargs="?", type=Path,
                        help="Optional existing GE-Proton11-7 ARM64 tool; otherwise detect or download it")
    locations = parser.add_mutually_exclusive_group()
    locations.add_argument("--steam-dir", type=Path, help="Steam installation directory")
    locations.add_argument("--compat-dir", type=Path, help="Steam compatibilitytools.d directory")
    parser.add_argument("--check", action="store_true",
                        help="Validate the base and release package without changing files")
    args = parser.parse_args(argv)
    package = Path(__file__).resolve().parent
    try:
        if sys.platform != "linux":
            raise InstallError("This compatibility tool requires Linux.")
        if os.geteuid() == 0:
            raise InstallError("Run this installer as your Steam user, without sudo.")
        validate_package(package)
        if args.base is not None and args.steam_dir is None and args.compat_dir is None:
            parent = args.base.expanduser().resolve(strict=True).parent
        else:
            parent = steam_compat_dir(args.steam_dir, args.compat_dir)
        target = destination(parent)
        base = args.base if args.base is not None else find_base(parent)
        if args.check:
            if base is None:
                raise InstallError(f"No matching GE-Proton11-7 ARM64 base is installed in {parent}. "
                                   "Run without --check to download and install it. No changes were made.")
            validate(base, package, parent)
            print(f"Validation passed. Installation would create: {target}")
        else:
            if base is None:
                target = install_download(package, parent)
            else:
                print(f"Using matching base: {base}")
                target = install(base, package, parent)
            print(f"Installed: {target}\n"
                  f"Restart Steam, then select {DISPLAY_NAME} for Gunfire Reborn.\n"
                  "No Steam, game, or FEX settings were changed.")
    except (InstallError, OSError, subprocess.CalledProcessError, tarfile.TarError,
            UnicodeError, urllib.error.URLError) as error:
        print(f"Installation stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
