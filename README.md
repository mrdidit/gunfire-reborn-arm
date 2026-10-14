# Gunfire Reborn ARM

Test build for Gunfire Reborn on ARM64 Linux. Tested on KPFE with Armada.

## Installation

1. Download and extract the package from [Releases](https://github.com/mrdidit/gunfire-reborn-arm/releases).
2. Close Steam. Open a terminal in the extracted folder and run:

   ```sh
   python3 install.py
   ```

3. Start Steam. Open Gunfire Reborn → Properties → Compatibility and select **GE ARM - Gunfire**.

The installer uses a matching GE-Proton11-7 ARM64 install if available. Otherwise it downloads the official ARM64 build, checks it, and sets up a separate tool. Existing Proton installs and game settings stay as they are.

Requires Steam, Python 3 and GNU coreutils. Run without `sudo`. For a custom Steam location, use `python3 install.py --steam-dir "/path/to/Steam"`.

## Status

The game loads and gameplay is working in testing. Full runs and map changes are not confirmed yet. Tested with FEX Fast.

To revert, select the original compatibility tool in Steam.

## Credits

Based on [GE-Proton11-7 ARM64](https://github.com/GloriousEggroll/proton-ge-custom/releases/tag/GE-Proton11-7) and FEX. Component licenses are in [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt) and `LICENSES/`.
