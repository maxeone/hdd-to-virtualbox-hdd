from __future__ import annotations

import ctypes
import json
from collections import deque
import queue
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = APP_DIR

BACKEND_DIR = RESOURCE_DIR / "backend"
RUNTIME_DIR = APP_DIR / "runtime"
DEFAULT_OUTPUT_DIR = APP_DIR.parent if not getattr(sys, "frozen", False) else APP_DIR


PRESETS = {
    "Windows 7 Legacy": {
        "firmware": "BIOS",
        "controller": "IDE",
        "chipset": "PIIX3",
        "guest_os": "Windows7_64",
        "repair": True,
        "patch_drivers": True,
        "reset_mounted_devices": True,
        "force_windows_boot": False,
        "run_chkdsk": False,
    },
    "Windows BIOS General": {
        "firmware": "BIOS",
        "controller": "SATA",
        "chipset": "PIIX3",
        "guest_os": "Windows10_64",
        "repair": True,
        "patch_drivers": True,
        "reset_mounted_devices": True,
        "force_windows_boot": False,
        "run_chkdsk": False,
    },
    "Windows UEFI General": {
        "firmware": "UEFI",
        "controller": "SATA",
        "chipset": "ICH9",
        "guest_os": "Windows10_64",
        "repair": True,
        "patch_drivers": True,
        "reset_mounted_devices": True,
        "force_windows_boot": False,
        "run_chkdsk": False,
    },
    "Custom": {
        "firmware": "Auto",
        "controller": "IDE",
        "chipset": "PIIX3",
        "guest_os": "Windows7_64",
        "repair": True,
        "patch_drivers": True,
        "reset_mounted_devices": True,
        "force_windows_boot": False,
        "run_chkdsk": False,
    },
}

FALLBACK_GUEST_OS_TYPES = [
    ("Other", "Other/Unknown"),
    ("Other_64", "Other/Unknown (64-bit)"),
    ("WindowsXP", "Windows XP (32-bit)"),
    ("WindowsXP_64", "Windows XP (64-bit)"),
    ("WindowsVista", "Windows Vista (32-bit)"),
    ("WindowsVista_64", "Windows Vista (64-bit)"),
    ("Windows7", "Windows 7 (32-bit)"),
    ("Windows7_64", "Windows 7 (64-bit)"),
    ("Windows8_64", "Windows 8 (64-bit)"),
    ("Windows81_64", "Windows 8.1 (64-bit)"),
    ("Windows10_64", "Windows 10 (64-bit)"),
    ("Windows11_64", "Windows 11 (64-bit)"),
    ("Windows2016_64", "Windows Server 2016 (64-bit)"),
    ("Windows2019_64", "Windows Server 2019 (64-bit)"),
    ("Windows2022_64", "Windows Server 2022 (64-bit)"),
    ("Ubuntu_64", "Ubuntu (64-bit)"),
    ("Debian_64", "Debian (64-bit)"),
    ("Fedora_64", "Fedora (64-bit)"),
    ("RedHat_64", "Red Hat (64-bit)"),
    ("ArchLinux_64", "Arch Linux (64-bit)"),
]

LANGUAGE_LABELS = {
    "English": "en",
    "Español": "es",
}

TRANSLATIONS = {
    "en": {
        "window_title": "VirtualBox Boot Builder",
        "admin_yes": "Administrator: yes",
        "admin_no": "Administrator: no",
        "reopen_admin": "Reopen as admin",
        "language": "Language",
        "admin_warning": "The app can inspect disks without elevation, but creating or repairing VHD images requires administrator rights.",
        "tab_source": "Source",
        "tab_process": "Process",
        "tab_vbox": "VirtualBox",
        "tab_log": "Log",
        "refresh_disks": "Refresh disks",
        "run_flow": "Run workflow",
        "source_disk": "Source disk",
        "refresh": "Refresh",
        "auto_select": "Auto-select suggested",
        "select_all": "Select all",
        "clear": "Clear",
        "preset": "Preset",
        "output_directory": "Output folder",
        "output_filename": "Output file name",
        "output_path": "Output VHD/VHDX",
        "browse": "Browse",
        "firmware": "Firmware",
        "boot_partition": "Boot partition",
        "windows_partition": "Windows partition",
        "flow_options": "Workflow options",
        "overwrite_output": "Overwrite output if it already exists",
        "repair_after_create": "Repair boot after creating the image",
        "force_windows_boot": "Force boot from the Windows partition",
        "patch_drivers": "Enable offline storage drivers",
        "reset_mounted_devices": "Reset MountedDevices",
        "run_chkdsk": "Run chkdsk during repair",
        "configure_vm": "Create or update a VirtualBox VM at the end",
        "vm_name": "VM name",
        "guest_os_type": "Guest OS type",
        "memory_mb": "Memory MB",
        "cpus": "CPUs",
        "disk_controller": "Disk controller",
        "chipset": "Chipset",
        "detach_disks": "Detach other virtual hard disks from the VM",
        "status_ready": "Ready",
        "status_reading_disks": "Reading disks...",
        "status_disks_updated": "Disks updated",
        "status_running": "Running...",
        "status_completed": "Completed",
        "status_error": "Error",
        "dialog_admin": "Administrator",
        "dialog_error": "Error",
        "dialog_validation": "Validation",
        "dialog_in_progress": "In progress",
        "dialog_completed": "Completed",
        "already_admin": "The app is already running as administrator.",
        "relaunch_failed": "Could not relaunch the app as administrator.",
        "save_image": "Save image",
        "all_files": "All files",
        "no_disks_found": "No disks were found.",
        "disk_no_name": "No name",
        "yes": "yes",
        "no": "no",
        "summary_disk": "Disk {disk_number}",
        "summary_name": "Name: {name}",
        "summary_bus": "Bus: {bus}",
        "summary_style": "Style: {style}",
        "summary_size": "Size: {size}",
        "summary_boot_host": "Host boot disk: {value}",
        "summary_system_host": "Host system disk: {value}",
        "summary_suggested_boot": "Suggested boot partition: {value}",
        "summary_suggested_windows": "Suggested Windows partition: {value}",
        "none": "none",
        "partition_header_select": "Sel",
        "partition_header_number": "#",
        "partition_header_letter": "Letter",
        "partition_header_fs": "FS",
        "partition_header_label": "Label",
        "partition_header_size": "Size",
        "partition_header_flags": "Flags",
        "partition_header_detected": "Detected",
        "detected_windows": "Windows",
        "detected_boot_bios": "Boot BIOS",
        "detected_boot_uefi": "Boot UEFI",
        "flag_active": "Active",
        "flag_boot": "Boot",
        "flag_system": "System",
        "must_run_admin": "Open the app as administrator before creating or repairing an image.",
        "select_disk_error": "Select a source disk.",
        "select_partition_error": "Select at least one partition.",
        "output_path_error": "Choose an output path.",
        "output_directory_error": "Choose an output folder.",
        "output_filename_error": "Choose an output file name.",
        "output_extension_error": "The output file must end in .vhd or .vhdx.",
        "output_on_source_disk_error": "The output folder is on the selected source disk. Choose a folder on a different disk.",
        "vm_name_error": "Enter the VM name.",
        "guest_os_error": "Choose a VirtualBox guest OS type.",
        "memory_error": "Memory must be a positive integer.",
        "cpu_error": "CPUs must be a positive integer.",
        "already_running": "A workflow is already running.",
        "preset_applied": "[preset] Applied: {preset}",
        "log_header": "=== VirtualBox Boot Builder ===",
        "log_preset": "Preset: {preset}",
        "log_disk": "Disk: {disk}",
        "log_partitions": "Partitions: {partitions}",
        "log_output": "Output: {output}",
        "log_completed": "=== Workflow completed ===",
        "completed_message": "The workflow finished successfully.",
        "run_script": ">>> Running {script}",
    },
    "es": {
        "window_title": "Constructor de Arranque para VirtualBox",
        "admin_yes": "Administrador: sí",
        "admin_no": "Administrador: no",
        "reopen_admin": "Reabrir como admin",
        "language": "Idioma",
        "admin_warning": "La app puede inspeccionar discos sin elevar, pero crear o reparar imágenes VHD requiere permisos de administrador.",
        "tab_source": "Origen",
        "tab_process": "Proceso",
        "tab_vbox": "VirtualBox",
        "tab_log": "Log",
        "refresh_disks": "Refrescar discos",
        "run_flow": "Ejecutar flujo",
        "source_disk": "Disco origen",
        "refresh": "Refrescar",
        "auto_select": "Auto-seleccionar sugeridas",
        "select_all": "Seleccionar todas",
        "clear": "Limpiar",
        "preset": "Preset",
        "output_directory": "Carpeta de salida",
        "output_filename": "Nombre del archivo de salida",
        "output_path": "Salida VHD/VHDX",
        "browse": "Examinar",
        "firmware": "Firmware",
        "boot_partition": "Partición de arranque",
        "windows_partition": "Partición de Windows",
        "flow_options": "Opciones del flujo",
        "overwrite_output": "Sobrescribir la salida si ya existe",
        "repair_after_create": "Reparar el arranque después de crear la imagen",
        "force_windows_boot": "Forzar arranque desde la partición de Windows",
        "patch_drivers": "Activar drivers de almacenamiento offline",
        "reset_mounted_devices": "Limpiar MountedDevices",
        "run_chkdsk": "Ejecutar chkdsk durante la reparación",
        "configure_vm": "Crear o actualizar una VM de VirtualBox al final",
        "vm_name": "Nombre de VM",
        "guest_os_type": "Tipo de SO invitado",
        "memory_mb": "Memoria MB",
        "cpus": "CPUs",
        "disk_controller": "Controlador de disco",
        "chipset": "Chipset",
        "detach_disks": "Desconectar otros discos duros virtuales de la VM",
        "status_ready": "Listo",
        "status_reading_disks": "Leyendo discos...",
        "status_disks_updated": "Discos actualizados",
        "status_running": "Ejecutando...",
        "status_completed": "Completado",
        "status_error": "Error",
        "dialog_admin": "Administrador",
        "dialog_error": "Error",
        "dialog_validation": "Validación",
        "dialog_in_progress": "En curso",
        "dialog_completed": "Completado",
        "already_admin": "La app ya está abierta como administrador.",
        "relaunch_failed": "No pude relanzar la app como administrador.",
        "save_image": "Guardar imagen",
        "all_files": "Todos los archivos",
        "no_disks_found": "No se encontraron discos.",
        "disk_no_name": "Sin nombre",
        "yes": "sí",
        "no": "no",
        "summary_disk": "Disco {disk_number}",
        "summary_name": "Nombre: {name}",
        "summary_bus": "Bus: {bus}",
        "summary_style": "Estilo: {style}",
        "summary_size": "Tamaño: {size}",
        "summary_boot_host": "Disco de arranque del host: {value}",
        "summary_system_host": "Disco de sistema del host: {value}",
        "summary_suggested_boot": "Partición sugerida de arranque: {value}",
        "summary_suggested_windows": "Partición sugerida de Windows: {value}",
        "none": "ninguna",
        "partition_header_select": "Sel",
        "partition_header_number": "#",
        "partition_header_letter": "Letra",
        "partition_header_fs": "FS",
        "partition_header_label": "Etiqueta",
        "partition_header_size": "Tamaño",
        "partition_header_flags": "Flags",
        "partition_header_detected": "Detectado",
        "detected_windows": "Windows",
        "detected_boot_bios": "Boot BIOS",
        "detected_boot_uefi": "Boot UEFI",
        "flag_active": "Activa",
        "flag_boot": "Boot",
        "flag_system": "System",
        "must_run_admin": "Abre la app como administrador antes de crear o reparar una imagen.",
        "select_disk_error": "Selecciona un disco origen.",
        "select_partition_error": "Selecciona al menos una partición.",
        "output_path_error": "Indica la ruta de salida.",
        "output_directory_error": "Indica la carpeta de salida.",
        "output_filename_error": "Indica el nombre del archivo de salida.",
        "output_extension_error": "El archivo de salida debe terminar en .vhd o .vhdx.",
        "output_on_source_disk_error": "La carpeta de salida esta en el mismo disco origen. Elige una carpeta en otro disco.",
        "vm_name_error": "Indica el nombre de la VM.",
        "guest_os_error": "Indica el tipo de SO invitado de VirtualBox.",
        "memory_error": "La memoria debe ser un entero positivo.",
        "cpu_error": "Los CPUs deben ser un entero positivo.",
        "already_running": "Ya hay un flujo ejecutándose.",
        "preset_applied": "[preset] Aplicado: {preset}",
        "log_header": "=== Constructor de Arranque para VirtualBox ===",
        "log_preset": "Preset: {preset}",
        "log_disk": "Disco: {disk}",
        "log_partitions": "Particiones: {partitions}",
        "log_output": "Salida: {output}",
        "log_completed": "=== Flujo completado ===",
        "completed_message": "El flujo terminó correctamente.",
        "run_script": ">>> Ejecutando {script}",
    },
}


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def human_size(size: int) -> str:
    if size is None:
        return "?"
    value = float(size)
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def ensure_runtime_dir() -> Path:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return RUNTIME_DIR


def format_guest_os_label(guest_os_id: str, description: str) -> str:
    return f"{guest_os_id} | {description}"


def relaunch_self_as_admin() -> bool:
    if is_admin():
        return True

    if getattr(sys, "frozen", False):
        executable = str(Path(sys.executable).resolve())
        parameters = ""
        workdir = str(APP_DIR)
    else:
        executable = "python"
        parameters = f'"{Path(__file__).resolve()}"'
        workdir = str(APP_DIR)

    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, parameters, workdir, 1)
    return result > 32


class VBoxBootBuilderApp:
    def current_language(self) -> str:
        return LANGUAGE_LABELS.get(getattr(self, "language_var", tk.StringVar(value="English")).get(), "en")

    def tr(self, key: str, **kwargs: str) -> str:
        language = self.current_language()
        text = TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text

    def load_guest_os_catalog(self) -> list[dict[str, str]]:
        candidates = [
            ["VBoxManage", "list", "ostypes"],
            [r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe", "list", "ostypes"],
        ]

        text = ""
        for cmd in candidates:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=15,
                    check=False,
                )
            except Exception:
                continue
            if result.stdout:
                text = result.stdout
                break

        if not text:
            return [{"id": guest_id, "description": description} for guest_id, description in FALLBACK_GUEST_OS_TYPES]

        catalog: list[dict[str, str]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("ID / Description:"):
                continue
            payload = line.split(":", 1)[1].strip()
            if " -- " in payload:
                guest_id, description = payload.split(" -- ", 1)
            else:
                parts = payload.split(None, 1)
                guest_id = parts[0]
                description = parts[1] if len(parts) > 1 else parts[0]
            catalog.append({"id": guest_id.strip(), "description": description.strip()})

        if not catalog:
            return [{"id": guest_id, "description": description} for guest_id, description in FALLBACK_GUEST_OS_TYPES]

        return catalog

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(TRANSLATIONS["en"]["window_title"])
        self.root.geometry("1280x900")
        self.root.minsize(1100, 760)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.disks: list[dict] = []
        self.partition_vars: dict[int, tk.BooleanVar] = {}
        self.selected_disk: dict | None = None
        self.guest_os_catalog = self.load_guest_os_catalog()
        self.guest_os_labels = [format_guest_os_label(item["id"], item["description"]) for item in self.guest_os_catalog]
        self.guest_os_label_to_id = {
            format_guest_os_label(item["id"], item["description"]): item["id"] for item in self.guest_os_catalog
        }

        self._build_vars()
        self._build_ui()
        self.root.after(100, self._flush_log_queue)
        ensure_runtime_dir()
        self.apply_preset(initial=True)
        self.refresh_disks()

    def _build_vars(self) -> None:
        self.language_var = tk.StringVar(value="English")
        self.admin_var = tk.StringVar()
        self.status_var = tk.StringVar(value=self.tr("status_ready"))
        self.preset_var = tk.StringVar(value="Windows 7 Legacy")
        self.disk_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=str(DEFAULT_OUTPUT_DIR))
        self.output_name_var = tk.StringVar(value="bootable-image.vhd")
        self.force_overwrite_var = tk.BooleanVar(value=True)
        self.repair_after_create_var = tk.BooleanVar(value=True)
        self.firmware_var = tk.StringVar(value="BIOS")
        self.boot_partition_var = tk.StringVar(value="Auto")
        self.windows_partition_var = tk.StringVar(value="Auto")
        self.force_windows_boot_var = tk.BooleanVar(value=False)
        self.patch_drivers_var = tk.BooleanVar(value=True)
        self.reset_mounted_devices_var = tk.BooleanVar(value=True)
        self.run_chkdsk_var = tk.BooleanVar(value=False)
        self.configure_vm_var = tk.BooleanVar(value=True)
        self.vm_name_var = tk.StringVar(value="ImportedWindows")
        self.guest_os_var = tk.StringVar(value="Windows7_64")
        self.memory_var = tk.StringVar(value="4096")
        self.cpu_var = tk.StringVar(value="2")
        self.controller_var = tk.StringVar(value="IDE")
        self.chipset_var = tk.StringVar(value="PIIX3")
        self.detach_disks_var = tk.BooleanVar(value=True)
        self.last_auto_output_name = "bootable-image.vhd"
        self.refresh_admin_label()

    def refresh_admin_label(self) -> None:
        self.admin_var.set(self.tr("admin_yes") if is_admin() else self.tr("admin_no"))

    def on_language_change(self, *_args: object) -> None:
        self.refresh_admin_label()
        self.rebuild_ui()

    def rebuild_ui(self) -> None:
        log_contents = ""
        current_tab = 0
        selected_disk_number = self.selected_disk["DiskNumber"] if self.selected_disk else None
        selected_partitions = self.selected_partition_numbers() if self.partition_vars else []
        boot_partition_value = self.boot_partition_var.get() if hasattr(self, "boot_partition_var") else "Auto"
        windows_partition_value = self.windows_partition_var.get() if hasattr(self, "windows_partition_var") else "Auto"
        force_windows_boot = self.force_windows_boot_var.get() if hasattr(self, "force_windows_boot_var") else False
        status_text = self.status_var.get() if hasattr(self, "status_var") else self.tr("status_ready")
        if hasattr(self, "log_text"):
            log_contents = self.log_text.get("1.0", "end-1c")
        if hasattr(self, "notebook"):
            try:
                current_tab = self.notebook.index(self.notebook.select())
            except Exception:
                current_tab = 0

        for child in self.root.winfo_children():
            child.destroy()

        self._build_ui()
        self.status_var.set(status_text)
        self.disk_combo["values"] = [self.disk_label(disk) for disk in self.disks]

        if selected_disk_number is not None:
            matching_disk = next((disk for disk in self.disks if disk["DiskNumber"] == selected_disk_number), None)
            if matching_disk:
                self.selected_disk = matching_disk
                self.disk_var.set(self.disk_label(matching_disk))
                self.on_disk_selected()
                for partition_number in selected_partitions:
                    if partition_number in self.partition_vars:
                        self.partition_vars[partition_number].set(True)
                if boot_partition_value in [str(part["PartitionNumber"]) for part in matching_disk.get("Partitions", [])] or boot_partition_value == "Auto":
                    self.boot_partition_var.set(boot_partition_value)
                if windows_partition_value in [str(part["PartitionNumber"]) for part in matching_disk.get("Partitions", [])] or windows_partition_value == "Auto":
                    self.windows_partition_var.set(windows_partition_value)
                self.force_windows_boot_var.set(force_windows_boot)

        if log_contents:
            self.log_text.insert("1.0", log_contents)
            self.log_text.see("end")
        try:
            self.notebook.select(current_tab)
        except Exception:
            pass

    def _build_ui(self) -> None:
        self.root.title(self.tr("window_title"))
        top = ttk.Frame(self.root, padding=12)
        top.pack(fill="x")

        ttk.Label(top, text=self.tr("window_title"), font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Label(top, textvariable=self.admin_var).pack(side="left", padx=(16, 0))
        ttk.Button(top, text=self.tr("reopen_admin"), command=self.relaunch_as_admin).pack(side="right")
        ttk.Label(top, text=self.tr("language")).pack(side="right", padx=(0, 8))
        self.language_combo = ttk.Combobox(top, textvariable=self.language_var, state="readonly", values=list(LANGUAGE_LABELS.keys()), width=12)
        self.language_combo.pack(side="right", padx=(0, 12))
        self.language_combo.bind("<<ComboboxSelected>>", self.on_language_change)

        if not is_admin():
            warning = ttk.Label(
                self.root,
                text=self.tr("admin_warning"),
                foreground="#a14f00",
                padding=(12, 0, 12, 8),
            )
            warning.pack(fill="x")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.source_tab = ttk.Frame(self.notebook, padding=12)
        self.process_tab = ttk.Frame(self.notebook, padding=12)
        self.vbox_tab = ttk.Frame(self.notebook, padding=12)
        self.log_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.source_tab, text=self.tr("tab_source"))
        self.notebook.add(self.process_tab, text=self.tr("tab_process"))
        self.notebook.add(self.vbox_tab, text=self.tr("tab_vbox"))
        self.notebook.add(self.log_tab, text=self.tr("tab_log"))

        self._build_source_tab()
        self._build_process_tab()
        self._build_vbox_tab()
        self._build_log_tab()

        bottom = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        bottom.pack(fill="x")
        self.progress = ttk.Progressbar(bottom, mode="indeterminate")
        self.progress.pack(side="left", fill="x", expand=True)
        ttk.Label(bottom, textvariable=self.status_var).pack(side="left", padx=(12, 0))
        ttk.Button(bottom, text=self.tr("refresh_disks"), command=self.refresh_disks).pack(side="right", padx=(8, 0))
        ttk.Button(bottom, text=self.tr("run_flow"), command=self.start_flow).pack(side="right")

    def _build_source_tab(self) -> None:
        controls = ttk.Frame(self.source_tab)
        controls.pack(fill="x")
        ttk.Label(controls, text=self.tr("source_disk")).grid(row=0, column=0, sticky="w")
        self.disk_combo = ttk.Combobox(controls, textvariable=self.disk_var, state="readonly", width=90)
        self.disk_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.disk_combo.bind("<<ComboboxSelected>>", lambda _event: self.on_disk_selected())
        ttk.Button(controls, text=self.tr("refresh"), command=self.refresh_disks).grid(row=1, column=1, sticky="ew")
        controls.columnconfigure(0, weight=1)

        self.disk_summary = tk.Text(self.source_tab, height=6, wrap="word")
        self.disk_summary.pack(fill="x", pady=(12, 12))
        self.disk_summary.configure(state="disabled")

        buttons = ttk.Frame(self.source_tab)
        buttons.pack(fill="x", pady=(0, 8))
        ttk.Button(buttons, text=self.tr("auto_select"), command=self.auto_select_partitions).pack(side="left")
        ttk.Button(buttons, text=self.tr("select_all"), command=self.select_all_partitions).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text=self.tr("clear"), command=self.clear_partitions).pack(side="left", padx=(8, 0))

        container = ttk.Frame(self.source_tab)
        container.pack(fill="both", expand=True)

        self.partition_canvas = tk.Canvas(container, highlightthickness=0)
        self.partition_scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.partition_canvas.yview)
        self.partition_frame = ttk.Frame(self.partition_canvas)

        self.partition_frame.bind(
            "<Configure>",
            lambda _event: self.partition_canvas.configure(scrollregion=self.partition_canvas.bbox("all")),
        )
        self.partition_canvas.create_window((0, 0), window=self.partition_frame, anchor="nw")
        self.partition_canvas.configure(yscrollcommand=self.partition_scrollbar.set)

        self.partition_canvas.pack(side="left", fill="both", expand=True)
        self.partition_scrollbar.pack(side="right", fill="y")

    def _build_process_tab(self) -> None:
        frame = self.process_tab
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text=self.tr("preset")).grid(row=0, column=0, sticky="w", pady=(0, 4))
        preset_combo = ttk.Combobox(frame, textvariable=self.preset_var, state="readonly", values=list(PRESETS))
        preset_combo.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        preset_combo.bind("<<ComboboxSelected>>", lambda _event: self.apply_preset())

        ttk.Label(frame, text=self.tr("output_directory")).grid(row=1, column=0, sticky="w", pady=(0, 4))
        output_row = ttk.Frame(frame)
        output_row.grid(row=1, column=1, sticky="ew", pady=(0, 8))
        output_row.columnconfigure(0, weight=1)
        ttk.Entry(output_row, textvariable=self.output_dir_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(output_row, text=self.tr("browse"), command=self.browse_output_directory).grid(row=0, column=1, padx=(8, 0))

        ttk.Label(frame, text=self.tr("output_filename")).grid(row=2, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(frame, textvariable=self.output_name_var).grid(row=2, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text=self.tr("firmware")).grid(row=3, column=0, sticky="w", pady=(0, 4))
        ttk.Combobox(frame, textvariable=self.firmware_var, state="readonly", values=["Auto", "BIOS", "UEFI"]).grid(row=3, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text=self.tr("boot_partition")).grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.boot_partition_combo = ttk.Combobox(frame, textvariable=self.boot_partition_var, state="readonly")
        self.boot_partition_combo.grid(row=4, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text=self.tr("windows_partition")).grid(row=5, column=0, sticky="w", pady=(0, 4))
        self.windows_partition_combo = ttk.Combobox(frame, textvariable=self.windows_partition_var, state="readonly")
        self.windows_partition_combo.grid(row=5, column=1, sticky="ew", pady=(0, 8))

        toggles = ttk.LabelFrame(frame, text=self.tr("flow_options"), padding=12)
        toggles.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        toggles.columnconfigure(0, weight=1)

        ttk.Checkbutton(toggles, text=self.tr("overwrite_output"), variable=self.force_overwrite_var).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(toggles, text=self.tr("repair_after_create"), variable=self.repair_after_create_var).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(toggles, text=self.tr("force_windows_boot"), variable=self.force_windows_boot_var).grid(row=2, column=0, sticky="w")
        ttk.Checkbutton(toggles, text=self.tr("patch_drivers"), variable=self.patch_drivers_var).grid(row=3, column=0, sticky="w")
        ttk.Checkbutton(toggles, text=self.tr("reset_mounted_devices"), variable=self.reset_mounted_devices_var).grid(row=4, column=0, sticky="w")
        ttk.Checkbutton(toggles, text=self.tr("run_chkdsk"), variable=self.run_chkdsk_var).grid(row=5, column=0, sticky="w")

    def _build_vbox_tab(self) -> None:
        frame = self.vbox_tab
        frame.columnconfigure(1, weight=1)

        ttk.Checkbutton(frame, text=self.tr("configure_vm"), variable=self.configure_vm_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(frame, text=self.tr("vm_name")).grid(row=1, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(frame, textvariable=self.vm_name_var).grid(row=1, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text=self.tr("guest_os_type")).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.guest_os_combo = ttk.Combobox(frame, textvariable=self.guest_os_var, values=self.guest_os_labels, state="normal")
        self.guest_os_combo.grid(row=2, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text=self.tr("memory_mb")).grid(row=3, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(frame, textvariable=self.memory_var).grid(row=3, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text=self.tr("cpus")).grid(row=4, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(frame, textvariable=self.cpu_var).grid(row=4, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text=self.tr("disk_controller")).grid(row=5, column=0, sticky="w", pady=(0, 4))
        ttk.Combobox(frame, textvariable=self.controller_var, state="readonly", values=["IDE", "SATA"]).grid(row=5, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text=self.tr("chipset")).grid(row=6, column=0, sticky="w", pady=(0, 4))
        ttk.Combobox(frame, textvariable=self.chipset_var, state="readonly", values=["PIIX3", "ICH9"]).grid(row=6, column=1, sticky="ew", pady=(0, 8))

        ttk.Checkbutton(frame, text=self.tr("detach_disks"), variable=self.detach_disks_var).grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _build_log_tab(self) -> None:
        self.log_text = tk.Text(self.log_tab, wrap="word")
        self.log_text.pack(fill="both", expand=True, side="left")
        log_scroll = ttk.Scrollbar(self.log_tab, orient="vertical", command=self.log_text.yview)
        log_scroll.pack(fill="y", side="right")
        self.log_text.configure(yscrollcommand=log_scroll.set)

    def relaunch_as_admin(self) -> None:
        if is_admin():
            messagebox.showinfo(self.tr("dialog_admin"), self.tr("already_admin"))
            return

        if not relaunch_self_as_admin():
            messagebox.showerror(self.tr("dialog_error"), self.tr("relaunch_failed"))
            return

        self.root.destroy()

    def append_log(self, text: str) -> None:
        self.log_text.insert("end", text)
        if not text.endswith("\n"):
            self.log_text.insert("end", "\n")
        self.log_text.see("end")

    def _flush_log_queue(self) -> None:
        try:
            while True:
                self.append_log(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._flush_log_queue)

    def log(self, text: str) -> None:
        self.log_queue.put(text)

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def browse_output_directory(self) -> None:
        initial_dir = self.output_dir_var.get().strip() or str(DEFAULT_OUTPUT_DIR)
        path = filedialog.askdirectory(title=self.tr("output_directory"), initialdir=initial_dir, mustexist=False)
        if path:
            self.output_dir_var.set(path)

    def get_output_path(self) -> str:
        output_dir = self.output_dir_var.get().strip()
        output_name = self.output_name_var.get().strip()
        if not output_dir or not output_name:
            return ""
        if Path(output_name).suffix == "":
            output_name = f"{output_name}.vhd"
        return str(Path(output_dir) / output_name)

    def find_disk_number_for_drive(self, drive: str) -> int | None:
        normalized = drive.rstrip(":\\").upper()
        for disk in self.disks:
            for partition in disk.get("Partitions", []):
                letter = (partition.get("DriveLetter") or "").rstrip(":\\").upper()
                if letter and letter == normalized:
                    return disk["DiskNumber"]
        return None

    def apply_preset(self, initial: bool = False) -> None:
        preset = PRESETS[self.preset_var.get()]
        self.firmware_var.set(preset["firmware"])
        self.controller_var.set(preset["controller"])
        self.chipset_var.set(preset["chipset"])
        self.set_guest_os_selection(preset["guest_os"])
        self.repair_after_create_var.set(preset["repair"])
        self.patch_drivers_var.set(preset["patch_drivers"])
        self.reset_mounted_devices_var.set(preset["reset_mounted_devices"])
        self.force_windows_boot_var.set(preset["force_windows_boot"])
        self.run_chkdsk_var.set(preset["run_chkdsk"])
        if not initial:
            self.log(self.tr("preset_applied", preset=self.preset_var.get()))

    def set_guest_os_selection(self, guest_os_id: str) -> None:
        for item in self.guest_os_catalog:
            if item["id"] == guest_os_id:
                self.guest_os_var.set(format_guest_os_label(item["id"], item["description"]))
                return
        self.guest_os_var.set(guest_os_id)

    def get_selected_guest_os_id(self) -> str:
        raw_value = self.guest_os_var.get().strip()
        if raw_value in self.guest_os_label_to_id:
            return self.guest_os_label_to_id[raw_value]
        if " | " in raw_value:
            return raw_value.split(" | ", 1)[0].strip()
        return raw_value

    def _powershell_command(self, script_path: Path, arguments: list[str]) -> list[str]:
        return [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            *arguments,
        ]

    def run_powershell_json(self, script_name: str, arguments: list[str] | None = None) -> object:
        script_path = BACKEND_DIR / script_name
        cmd = self._powershell_command(script_path, arguments or [])
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"Fallo al ejecutar {script_name}")
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            return [data]
        return data

    def refresh_disks(self) -> None:
        self.set_status(self.tr("status_reading_disks"))
        try:
            disks = self.run_powershell_json("list-disks.ps1")
        except Exception as exc:
            self.set_status(self.tr("status_error"))
            messagebox.showerror(self.tr("dialog_error"), str(exc))
            return

        self.disks = disks
        values = [self.disk_label(disk) for disk in disks]
        self.disk_combo["values"] = values
        if values:
            if self.disk_var.get() not in values:
                self.disk_var.set(values[0])
            self.on_disk_selected()
        else:
            self.disk_var.set("")
            self.clear_partition_frame()
            self._set_disk_summary(self.tr("no_disks_found"))
        self.set_status(self.tr("status_disks_updated"))

    def disk_label(self, disk: dict) -> str:
        return f'Disk {disk["DiskNumber"]} | {disk.get("FriendlyName") or self.tr("disk_no_name")} | {disk.get("BusType")} | {disk.get("PartitionStyle")} | {human_size(disk.get("Size", 0))}'

    def get_selected_disk(self) -> dict | None:
        label = self.disk_var.get()
        for disk in self.disks:
            if self.disk_label(disk) == label:
                return disk
        return None

    def on_disk_selected(self) -> None:
        disk = self.get_selected_disk()
        self.selected_disk = disk
        if not disk:
            return

        self.vm_name_var.set(f"Disk{disk['DiskNumber']}_Imported")
        default_name = f"disk{disk['DiskNumber']}-bootable.vhd"
        current_output_name = self.output_name_var.get().strip()
        if not current_output_name or current_output_name == self.last_auto_output_name:
            self.output_name_var.set(default_name)
            self.last_auto_output_name = default_name

        summary_lines = [
            self.tr("summary_disk", disk_number=disk["DiskNumber"]),
            self.tr("summary_name", name=disk.get("FriendlyName") or self.tr("disk_no_name")),
            self.tr("summary_bus", bus=disk.get("BusType")),
            self.tr("summary_style", style=disk.get("PartitionStyle")),
            self.tr("summary_size", size=human_size(disk.get("Size", 0))),
            self.tr("summary_boot_host", value=self.tr("yes") if disk.get("IsBoot") else self.tr("no")),
            self.tr("summary_system_host", value=self.tr("yes") if disk.get("IsSystem") else self.tr("no")),
            self.tr("summary_suggested_boot", value=disk.get("SuggestedBootPartition") or self.tr("none")),
            self.tr("summary_suggested_windows", value=disk.get("SuggestedWindowsPartition") or self.tr("none")),
        ]
        self._set_disk_summary("\n".join(summary_lines))
        self.rebuild_partition_frame(disk)
        self.refresh_partition_combos(disk)
        self.auto_select_partitions()

        if disk.get("PartitionStyle") == "GPT" and self.preset_var.get() == "Windows 7 Legacy":
            self.preset_var.set("Windows UEFI General")
            self.apply_preset()

    def _set_disk_summary(self, text: str) -> None:
        self.disk_summary.configure(state="normal")
        self.disk_summary.delete("1.0", "end")
        self.disk_summary.insert("1.0", text)
        self.disk_summary.configure(state="disabled")

    def clear_partition_frame(self) -> None:
        for widget in self.partition_frame.winfo_children():
            widget.destroy()
        self.partition_vars.clear()

    def rebuild_partition_frame(self, disk: dict) -> None:
        self.clear_partition_frame()

        header = [
            self.tr("partition_header_select"),
            self.tr("partition_header_number"),
            self.tr("partition_header_letter"),
            self.tr("partition_header_fs"),
            self.tr("partition_header_label"),
            self.tr("partition_header_size"),
            self.tr("partition_header_flags"),
            self.tr("partition_header_detected"),
        ]
        for col, label in enumerate(header):
            ttk.Label(self.partition_frame, text=label, font=("Segoe UI", 9, "bold")).grid(row=0, column=col, sticky="w", padx=4, pady=(0, 6))

        for row_index, partition in enumerate(disk.get("Partitions", []), start=1):
            partition_number = partition["PartitionNumber"]
            var = tk.BooleanVar(value=False)
            self.partition_vars[partition_number] = var

            detected = []
            if partition.get("HasWindows"):
                detected.append(self.tr("detected_windows"))
            if partition.get("HasBootMgr") or partition.get("HasBootFolder"):
                detected.append(self.tr("detected_boot_bios"))
            if partition.get("HasEfiBoot"):
                detected.append(self.tr("detected_boot_uefi"))

            flags = []
            if partition.get("IsActive"):
                flags.append(self.tr("flag_active"))
            if partition.get("IsBoot"):
                flags.append(self.tr("flag_boot"))
            if partition.get("IsSystem"):
                flags.append(self.tr("flag_system"))

            ttk.Checkbutton(self.partition_frame, variable=var).grid(row=row_index, column=0, sticky="w", padx=4, pady=2)
            ttk.Label(self.partition_frame, text=str(partition_number)).grid(row=row_index, column=1, sticky="w", padx=4, pady=2)
            ttk.Label(self.partition_frame, text=partition.get("DriveLetter") or "-").grid(row=row_index, column=2, sticky="w", padx=4, pady=2)
            ttk.Label(self.partition_frame, text=partition.get("FileSystem") or "-").grid(row=row_index, column=3, sticky="w", padx=4, pady=2)
            ttk.Label(self.partition_frame, text=partition.get("FileSystemLabel") or "-").grid(row=row_index, column=4, sticky="w", padx=4, pady=2)
            ttk.Label(self.partition_frame, text=human_size(partition.get("Size", 0))).grid(row=row_index, column=5, sticky="w", padx=4, pady=2)
            ttk.Label(self.partition_frame, text=", ".join(flags) if flags else "-").grid(row=row_index, column=6, sticky="w", padx=4, pady=2)
            ttk.Label(self.partition_frame, text=", ".join(detected) if detected else "-").grid(row=row_index, column=7, sticky="w", padx=4, pady=2)

    def refresh_partition_combos(self, disk: dict) -> None:
        values = ["Auto"] + [str(part["PartitionNumber"]) for part in disk.get("Partitions", [])]
        self.boot_partition_combo["values"] = values
        self.windows_partition_combo["values"] = values
        self.boot_partition_var.set("Auto")
        self.windows_partition_var.set("Auto")

    def auto_select_partitions(self) -> None:
        if not self.selected_disk:
            return

        self.clear_partitions()
        boot_number = self.selected_disk.get("SuggestedBootPartition")
        windows_number = self.selected_disk.get("SuggestedWindowsPartition")

        if boot_number in self.partition_vars:
            self.partition_vars[boot_number].set(True)
            self.boot_partition_var.set(str(boot_number))
        else:
            self.boot_partition_var.set("Auto")

        if windows_number in self.partition_vars:
            self.partition_vars[windows_number].set(True)
            self.windows_partition_var.set(str(windows_number))
        else:
            self.windows_partition_var.set("Auto")

        if boot_number == windows_number and windows_number in self.partition_vars:
            self.force_windows_boot_var.set(True)

    def select_all_partitions(self) -> None:
        for var in self.partition_vars.values():
            var.set(True)

    def clear_partitions(self) -> None:
        for var in self.partition_vars.values():
            var.set(False)

    def selected_partition_numbers(self) -> list[int]:
        return sorted(number for number, var in self.partition_vars.items() if var.get())

    def validate_inputs(self) -> None:
        if not is_admin():
            raise RuntimeError(self.tr("must_run_admin"))

        if not self.selected_disk:
            raise RuntimeError(self.tr("select_disk_error"))

        selected_partitions = self.selected_partition_numbers()
        if not selected_partitions:
            raise RuntimeError(self.tr("select_partition_error"))

        output_dir = self.output_dir_var.get().strip()
        output_name = self.output_name_var.get().strip()
        output_path = self.get_output_path()
        if not output_dir:
            raise RuntimeError(self.tr("output_directory_error"))
        if not output_name:
            raise RuntimeError(self.tr("output_filename_error"))
        if not output_path:
            raise RuntimeError(self.tr("output_path_error"))
        if Path(output_path).suffix.lower() not in {".vhd", ".vhdx"}:
            raise RuntimeError(self.tr("output_extension_error"))

        output_drive = Path(output_path).drive
        if output_drive:
            output_disk_number = self.find_disk_number_for_drive(output_drive)
            if output_disk_number is not None and output_disk_number == self.selected_disk["DiskNumber"]:
                raise RuntimeError(self.tr("output_on_source_disk_error"))

        if self.configure_vm_var.get():
            if not self.vm_name_var.get().strip():
                raise RuntimeError(self.tr("vm_name_error"))
            if not self.get_selected_guest_os_id():
                raise RuntimeError(self.tr("guest_os_error"))
            if not self.memory_var.get().isdigit() or int(self.memory_var.get()) <= 0:
                raise RuntimeError(self.tr("memory_error"))
            if not self.cpu_var.get().isdigit() or int(self.cpu_var.get()) <= 0:
                raise RuntimeError(self.tr("cpu_error"))

    def start_flow(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo(self.tr("dialog_in_progress"), self.tr("already_running"))
            return

        try:
            self.validate_inputs()
        except Exception as exc:
            messagebox.showerror(self.tr("dialog_validation"), str(exc))
            return

        self.log_text.delete("1.0", "end")
        self.status_var.set(self.tr("status_running"))
        self.progress.start(8)
        self.worker_thread = threading.Thread(target=self._run_flow_worker, daemon=True)
        self.worker_thread.start()

    def _run_flow_worker(self) -> None:
        try:
            self.log(self.tr("log_header"))
            self.log(self.tr("log_preset", preset=self.preset_var.get()))
            self.log(self.tr("log_disk", disk=self.disk_label(self.selected_disk)))
            self.log(self.tr("log_partitions", partitions=", ".join(map(str, self.selected_partition_numbers()))))
            output_path = self.get_output_path()
            self.log(self.tr("log_output", output=output_path))

            create_args = [
                "-DiskNumber",
                str(self.selected_disk["DiskNumber"]),
                "-PartitionNumbers",
                ",".join(str(x) for x in self.selected_partition_numbers()),
                "-OutputPath",
                output_path,
                "-ToolsDir",
                str(ensure_runtime_dir() / "tools"),
            ]
            if self.force_overwrite_var.get():
                create_args.append("-ForceOverwrite")

            self._run_script_with_live_output("create-vhd.ps1", create_args)

            if self.repair_after_create_var.get():
                repair_args = [
                    "-VhdPath",
                    output_path,
                    "-FirmwareMode",
                    self.firmware_var.get(),
                ]
                if self.boot_partition_var.get() != "Auto":
                    repair_args.extend(["-BootPartitionNumber", self.boot_partition_var.get()])
                if self.windows_partition_var.get() != "Auto":
                    repair_args.extend(["-WindowsPartitionNumber", self.windows_partition_var.get()])
                if self.force_windows_boot_var.get():
                    repair_args.append("-ForceWindowsPartitionBoot")
                if not self.patch_drivers_var.get():
                    repair_args.append("-SkipStorageDriverPatch")
                if not self.reset_mounted_devices_var.get():
                    repair_args.append("-SkipMountedDevicesReset")
                if self.run_chkdsk_var.get():
                    repair_args.append("-RunChkdsk")

                self._run_script_with_live_output("repair-vhd.ps1", repair_args)

            if self.configure_vm_var.get():
                configure_args = [
                    "-VhdPath",
                    output_path,
                    "-VmName",
                    self.vm_name_var.get().strip(),
                    "-GuestOSType",
                    self.get_selected_guest_os_id(),
                    "-FirmwareMode",
                    "BIOS" if self.firmware_var.get() == "Auto" else self.firmware_var.get(),
                    "-StorageController",
                    self.controller_var.get(),
                    "-Chipset",
                    self.chipset_var.get(),
                    "-MemoryMB",
                    self.memory_var.get().strip(),
                    "-CpuCount",
                    self.cpu_var.get().strip(),
                ]
                if self.detach_disks_var.get():
                    configure_args.append("-DetachExistingHardDisks")

                self._run_script_with_live_output("configure-vbox-vm.ps1", configure_args)

            self.log(self.tr("log_completed"))
            self.root.after(0, lambda: messagebox.showinfo(self.tr("dialog_completed"), self.tr("completed_message")))
            self.root.after(0, lambda: self.set_status(self.tr("status_completed")))
        except Exception as exc:
            self.log("")
            self.log(f"[ERROR] {exc}")
            self.root.after(0, lambda: messagebox.showerror(self.tr("dialog_error"), str(exc)))
            self.root.after(0, lambda: self.set_status(self.tr("status_error")))
        finally:
            self.root.after(0, self.progress.stop)

    def _run_script_with_live_output(self, script_name: str, arguments: list[str]) -> None:
        script_path = BACKEND_DIR / script_name
        self.log("")
        self.log(self.tr("run_script", script=script_name))
        cmd = self._powershell_command(script_path, arguments)
        output_tail: deque[str] = deque(maxlen=25)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            clean_line = line.rstrip()
            output_tail.append(clean_line)
            self.log(clean_line)
        process.wait()
        if process.returncode != 0:
            tail_text = "\n".join(item for item in output_tail if item)
            if tail_text:
                raise RuntimeError(f"{script_name} fallo con codigo {process.returncode}.\n\n{tail_text}")
            raise RuntimeError(f"{script_name} fallo con codigo {process.returncode}.")


def main() -> None:
    if not is_admin():
        if relaunch_self_as_admin():
            return
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    app = VBoxBootBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
