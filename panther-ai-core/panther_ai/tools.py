import os
import platform
import shutil
import subprocess

TOOL_REGISTRY = {
    "system_info": {"name": "system_info", "description": "Read safe host system information", "risk": "read"},
    "disk_usage": {"name": "disk_usage", "description": "Read filesystem usage", "risk": "read"},
    "docker_ps": {"name": "docker_ps", "description": "List running Docker containers", "risk": "read"},
}

def run_tool(name, args):
    if name == "system_info":
        return {
            "hostname": platform.node(),
            "kernel": platform.release(),
            "os": platform.platform(),
            "cpu_count": os.cpu_count(),
        }
    if name == "disk_usage":
        path = args.get("path", "/")
        return {"path": path, "usage": shutil.disk_usage(path)._asdict()}
    if name == "docker_ps":
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}"], capture_output=True, text=True, timeout=10)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "docker command failed")
        rows = []
        for line in result.stdout.splitlines():
            name_, image, status = line.split("|", 2)
            rows.append({"name": name_, "image": image, "status": status})
        return {"containers": rows}
    raise ValueError("Unknown tool")
