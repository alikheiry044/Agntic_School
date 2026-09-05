import os

# فایل‌هایی که کدهای اصلی توشون هستن
IGNORE_DIRS = {".idea", ".venv", "__pycache__", "Scratches"}
VALID_EXTENSIONS = {".py", ".env", ".json", ".sql", ".md"}

output_file = "all_project_code.txt"

with open(output_file, "w", encoding="utf-8") as outfile:
    for root, dirs, files in os.walk("."):
        # حذف پوشه‌های غیرضروری از جستجو
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file == "export.py" or file == output_file:
                continue

            ext = os.path.splitext(file)[1]
            if ext in VALID_EXTENSIONS or file == ".env":
                file_path = os.path.join(root, file)
                outfile.write(f"\n{'='*60}\n")
                outfile.write(f"FILE: {file_path}\n")
                outfile.write(f"{'='*60}\n\n")

                try:
                    with open(file_path, "r", encoding="utf-8") as infile:
                        outfile.write(infile.read())
                        outfile.write("\n")
                except Exception as e:
                    outfile.write(f"Error reading file: {e}\n")

print(
    f"تمام کدهای پوشه app و فایل‌های اصلی در '{output_file}' ذخیره شدند!"
)