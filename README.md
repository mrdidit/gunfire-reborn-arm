# GE-Proton11-7-Reborn1

Gunfire Reborn test build for ARM64 Linux. Tested on KPFE with Armada.

## Install

Requires ARM64 Linux, Steam and **Steam Linux Runtime 4.0 - Arm64** (App ID `4185400`, available in Steam's Library under Tools).

1. Download [GE-Proton11-7-Reborn1-arm64.tar.gz](https://github.com/mrdidit/gunfire-reborn-arm/releases/download/Reborn1/GE-Proton11-7-Reborn1-arm64.tar.gz) and extract it into Steam's `compatibilitytools.d` folder. On Armada this is normally `~/.local/share/Steam/compatibilitytools.d/`. Create the folder if it is missing.
2. Restart Steam. Open Gunfire Reborn → Properties → Compatibility and select **GE-Proton11-7-Reborn1 (ARM64)**.
3. Use the launch options below for your device.

This is the complete Proton tool. No separate installer or manual Python setup is needed. Keep the original Proton tool installed if you want to switch back.

## FEX settings

The tested FEX configuration is **Fast with TSO enabled**:

| Setting | Value |
| --- | --- |
| TSO | On |
| Vector TSO | Off |
| Memcpy/Set TSO | Off |
| Half-barrier TSO | Off |
| Reduced x87 precision | On |
| Multiblock | On |

## Steam launch options

**Steam Frame:** use this entire line. It applies all six FEX settings directly, so no preset menu is needed:

```sh
PROTON_NO_FSYNC=1 PROTON_LOG=0 FEX_TSOENABLED=1 FEX_VECTORTSOENABLED=0 FEX_MEMCPYSETTSOENABLED=0 FEX_HALFBARRIERTSOENABLED=0 FEX_X87REDUCEDPRECISION=1 FEX_MULTIBLOCK=1 %command%
```

**Armada:** set Gunfire's per-game FEX preset to **Custom**, with the toggles shown above, then use:

```sh
PROTON_NO_FSYNC=1 /usr/libexec/armada/armada-game-launch %command%
```

The Armada launcher applies the per-game FEX settings. Diagnostic logging is off by default.

## Test status

**14 October 2026, KPFE with Armada:** First and second maps completed, with no crash reported so far. A full run is not confirmed yet.

**Steam Frame:** Launch reported with the bundled defaults and no launch options. Sustained gameplay is not confirmed yet.

Reported setup: performance mode, slight CPU underclock, GPU limited to **222 MHz**, **720p**, medium/high graphics, steady **72 FPS**. These are test settings, not required clock limits.

## Credits

Maintained by **Mr. Didi / Grinding Reborn**. Based on **GE-Proton11-7 ARM64** and FEX. Component notices and source references are included with the tool.
