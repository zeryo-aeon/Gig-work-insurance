import os

def read_project():
    root_dir = "."
    exclude_dirs = {".git", ".github", "env", "__pycache__", ".pytest_cache"}
    exclude_files = {".cache.sqlite", "demo.mp4", "demo2.mp4", "riskassement.png", "savingbuffer.png"}
    text_extensions = {".py", ".html", ".css", ".js", ".md", ".txt", ".json", ".env"}

    print(f"# Project Content Summary - {os.path.abspath(root_dir)}\n")

    for root, dirs, files in os.walk(root_dir):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file in exclude_files:
                continue
                
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            
            if ext in text_extensions:
                print(f"\n{'='*80}")
                print(f"FILE: {file_path}")
                print(f"{'='*80}\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        print(f.read())
                except Exception as e:
                    print(f"[Error reading file: {e}]")

if __name__ == "__main__":
    read_project()
