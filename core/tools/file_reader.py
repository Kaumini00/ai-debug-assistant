def read_file(path: str) -> str:
    try:
        with open(path, "r", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        return f"[Error] File not found: {path}"
    except Exception as e:
        return f"[Error] Could not read file: {e}"