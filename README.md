# HDD to VirtualBox HDD

HDD to VirtualBox HDD is a Windows GUI utility for turning an existing Windows installation on a physical, USB, or external disk into a VirtualBox-bootable image.

It was created to emulate an external Windows 7 hard drive with preloaded software inside VirtualBox, so legacy environments can be tested safely without modifying the original disk.

Spanish instructions: see [LEEME.md](LEEME.md).

The desktop application in this repository is named `VirtualBox Boot Builder`. It automates a workflow that usually requires several manual steps:

- inspect disks and partitions
- pick the boot and Windows partitions
- create a `VHD` or `VHDX` with Sysinternals `Disk2vhd`
- repair offline boot files
- patch offline storage drivers to reduce `STOP 0x7B`
- optionally create or update a VirtualBox VM and attach the image

This makes the project especially useful for Windows 7 testing, legacy software validation, external HDD virtualization, USB disk migration, and trial runs of old line-of-business systems that still depend on a preconfigured environment.

## Common Use Cases

- Emulate an external Windows 7 HDD in VirtualBox
- Boot a USB Windows disk with preinstalled software for testing
- Preserve a legacy Windows 7 environment before migration
- Validate old business, lab, industrial, or service software in a VM
- Clone a physical Windows disk into a VirtualBox-readable VHD or VHDX

## Main Features

- Disk and partition discovery from a GUI
- Suggested partition selection for common BIOS and UEFI layouts
- Presets for legacy Windows 7, generic BIOS installs, and generic UEFI installs
- Configurable firmware mode, controller type, chipset, memory, CPUs, and VirtualBox guest OS type
- Live execution log
- Automatic elevation to administrator by default
- English UI by default with optional Spanish switch

## Requirements

- Windows
- Administrator rights
- Python 3.13+ if you run the `.py` version
- VirtualBox installed if you want the app to configure a VM automatically
- Internet access on first image creation if `Disk2vhd` has not been downloaded yet

## Launching

Portable executable:

- `portable/VirtualBoxBootBuilder/VirtualBoxBootBuilder.exe`

Source version:

- `run-virtualbox-boot-builder.cmd`
- or `python vbox_boot_builder\virtualbox_boot_builder.py`

The app requests elevation automatically. The packaged `.exe` is also built with an admin manifest.

## Typical Workflow

1. Open the app as administrator.
2. Select the source disk.
3. Keep the suggested boot and Windows partitions, or adjust them manually.
4. Choose an output `VHD` or `VHDX`.
5. Keep repair enabled unless you explicitly want raw capture only.
6. In the VirtualBox tab, choose the guest OS type and VM settings.
7. Run the workflow.

## Notes

- Legacy BIOS Windows installs often need both the small boot partition and the main Windows partition.
- If a copied Windows system still stops with `0x7B`, the app attempts an offline storage-driver patch and clears `MountedDevices`.
- For older Windows versions, `IDE` is often more compatible than `SATA`.
- Some systems may still require Startup Repair from a Windows ISO or `sysprep /generalize` on the original machine.

## Project Layout

- `vbox_boot_builder/virtualbox_boot_builder.py`: main GUI app
- `vbox_boot_builder/backend/list-disks.ps1`: disk inventory
- `vbox_boot_builder/backend/create-vhd.ps1`: image creation
- `vbox_boot_builder/backend/repair-vhd.ps1`: boot repair and driver patching
- `vbox_boot_builder/backend/configure-vbox-vm.ps1`: VirtualBox VM setup
- `build-virtualbox-boot-builder-exe.ps1`: PyInstaller build script

## Building the EXE

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build-virtualbox-boot-builder-exe.ps1
```

The build script produces a Windows executable in `portable/VirtualBoxBootBuilder/`.
