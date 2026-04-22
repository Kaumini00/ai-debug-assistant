import os

def search_code(directory: str, keyword: str) -> list:
    matches = []
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path, errors="ignore") as f:
                        for i, line in enumerate(f):
                            if keyword.lower() in line.lower():
                                matches.append({
                                    "file": path,
                                    "line": i + 1,
                                    "content": line.strip()
                                })
    except Exception as e:
        return [{"error": str(e)}]
    return matches