# GE-Proton11-7-Reborn1 (ARM64)

**Reborn1 is a patched build of GE-Proton11-7 ARM64**, with a FEX runtime compatibility fix developed and tested using Gunfire Reborn. GE-Proton is the base; Reborn1 identifies this custom revision. It is packaged as a complete Steam compatibility tool for compatible **ARM64 Linux systems**, including handhelds and other ARM64 devices.

**It is not limited to KPFE or Steam Frame.** Those are the devices used for testing so far. Other devices need a working ARM64 Steam/Proton environment and suitable graphics drivers; results on additional hardware still need testing.

## What Reborn1 changes

The ARM Proton builds tested during development closed Gunfire Reborn at the loading screen, before gameplay. Reborn1 includes a modified **FEX ARM64EC translation runtime** that addresses the startup compatibility issue behind that failure.

The fix adjusts how the runtime handles memory permissions and updates to executable code during game initialization. This allows a startup operation that previously failed to complete, so the game can reach gameplay using ARM Proton. The change is included in the downloaded tool; users do not need to patch files themselves.

It installs alongside other Proton versions and can be selected per game in Steam. The build can also be selected for other games; Gunfire Reborn is the current test case, and results for other games have not yet been validated.

## Install

Requires an ARM64 Linux Steam setup capable of running ARM64 Proton, working graphics drivers, and **Steam Linux Runtime 4.0 - Arm64** (App ID `4185400`, available in Steam's Library under Tools).

1. Download [GE-Proton11-7-Reborn1-arm64.tar.gz](https://github.com/mrdidit/gunfire-reborn-arm/releases/download/Reborn1/GE-Proton11-7-Reborn1-arm64.tar.gz) and extract it into Steam's `compatibilitytools.d` folder. On Armada this is normally `~/.local/share/Steam/compatibilitytools.d/`. Create the folder if it is missing.
2. Restart Steam. Open Gunfire Reborn → Properties → Compatibility and select **GE-Proton11-7-Reborn1 (ARM64)**.
3. Use the standard ARM64 launch options below, or the Armada preset workflow if your system provides it.

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

**Standard ARM64 Linux setup, including Steam Frame:** use this entire line. It applies all six tested FEX settings directly, so no preset menu is needed:

```sh
PROTON_NO_FSYNC=1 PROTON_LOG=0 FEX_TSOENABLED=1 FEX_VECTORTSOENABLED=0 FEX_MEMCPYSETTSOENABLED=0 FEX_HALFBARRIERTSOENABLED=0 FEX_X87REDUCEDPRECISION=1 FEX_MULTIBLOCK=1 %command%
```

**Armada:** set Gunfire's per-game FEX preset to **Custom**, with the toggles shown above, then use:

```sh
PROTON_NO_FSYNC=1 /usr/libexec/armada/armada-game-launch %command%
```

The Armada launcher applies the per-game FEX settings. Both launch commands disable fsync to match the tested configuration. Diagnostic logging is off by default.

## Test status

Reported gameplay results as of **14 October 2026**. These are the tested devices; the build is not restricted to either model or chipset.

| Device | Processor | OS used | Gunfire Reborn result |
| --- | --- | --- | --- |
| [KONKR Pocket FIT Elite (KPFE)](https://www.ayaneo.jp/konkr-pocket-fit) | Qualcomm Snapdragon 8 Elite | Armada Linux | First and second maps completed without a reported crash. Full run not yet confirmed. |
| [Steam Frame](https://partner.steamgames.com/doc/steamhardware/steamframe/compatibility) | Qualcomm Snapdragon 8 Gen 3 | SteamOS | Launch reported with bundled defaults and no launch options. Sustained gameplay not yet confirmed. |

Reported KPFE setup: performance mode, slight CPU underclock, GPU limited to **222 MHz**, **720p**, medium/high graphics, steady **72 FPS**. These are user-reported results from that setup, not required clock limits or a performance guarantee for other hardware.

For reports from other devices, include the device and OS, selected Proton version, FEX settings, launch options, and how far the game ran. This helps distinguish startup success from a completed gameplay session.

## Credits

Maintained by **mrdidit**. Based on **GE-Proton11-7 ARM64** and FEX. Component notices and source references are included with the tool.
