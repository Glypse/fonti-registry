import json
from pathlib import Path
from typing import Dict, Optional

from bs4 import BeautifulSoup
from rich.console import Console

console = Console()

BASE_PATH = Path(__file__).parent / "google-fonts"
DIRS = ["ofl", "apache", "ufl"]


def get_html_path(dir_name: str, font_name: str) -> Optional[Path]:
    """
    Get the path to the HTML file for a given directory and font name.
    First tries article/ARTICLE.en_us.html, then DESCRIPTION.en_us.html.
    Returns None if neither exists.
    """
    article_path = BASE_PATH / dir_name / font_name / "article" / "ARTICLE.en_us.html"
    if article_path.exists():
        return article_path

    desc_path = BASE_PATH / dir_name / font_name / "DESCRIPTION.en_us.html"
    if desc_path.exists():
        return desc_path

    return None


def extract_github_link(file_path: Path) -> Optional[str]:
    """
    Extract the first GitHub link from an HTML file.
    Returns the href if found, None otherwise.
    """
    with open(file_path, encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    links = soup.find_all("a", href=True)
    github_links = [link["href"] for link in links if "github.com" in link["href"]]
    if github_links:
        return str(github_links[0])  # Ensure it's a string
    return None


def get_metadata_entries(metadata_path: Path, entries: list[str]) -> list[str]:
    """
    Extract specified entries from METADATA.pb file.
    Returns a list of values in the same order as entries, empty string if not found.
    """
    if not metadata_path.exists():
        return [""] * len(entries)
    values: Dict[str, str] = {}
    try:
        with open(metadata_path, encoding="utf-8") as f:
            for line in f:
                for entry in entries:
                    if line.startswith(f"{entry}:"):
                        # Extract the value after "entry:"
                        value = line.split(":", 1)[1].strip().strip('"')
                        values[entry] = value
                        break
    except Exception:
        pass
    return [values.get(entry, "") for entry in entries]


def main() -> None:
    """
    Main function to scan all font directories and build a JSON mapping
    of font names to their metadata (name, display_name, and link).
    """
    font_data: Dict[str, Dict[str, str]] = {}

    for dir_name in DIRS:
        dir_path = BASE_PATH / dir_name
        if not dir_path.exists():
            console.print(
                f"[yellow]Directory {dir_path} does not exist, skipping.[/yellow]"
            )
            continue

        for subdir in dir_path.iterdir():
            if not subdir.is_dir():
                continue

            font_name = subdir.name
            html_path = get_html_path(dir_name, font_name)
            link = ""
            if html_path:
                extracted_link = extract_github_link(html_path)
                if extracted_link:
                    link = extracted_link

            metadata_path = subdir / "METADATA.pb"
            values = get_metadata_entries(metadata_path, ["name", "display_name"])
            name = values[0]
            display_name = values[1]

            font_data[font_name] = {
                "name": name,
                "display_name": display_name,
                "link": link,
            }
            console.print(
                f"[green]Processed {font_name}: name='{name}', display_name='{display_name}', link='{link}'[/green]"
            )

    # Output the results to a JSON file
    output_file = Path(__file__).parent / "registry" / "fonti_registry.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(font_data, f, separators=(",", ":"), indent=None)
        # json.dump(font_data, f, indent=4)

    console.print(f"[green]Saved {len(font_data)} fonts to {output_file}[/green]")


if __name__ == "__main__":
    main()
