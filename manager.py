import click, os, sys
from pathlib import Path
from rich import print
from rich.panel import Panel
from rich.padding import Padding
from rich.table import Table
from rich.console import Console
from rich.theme import Theme
from pyfiglet import Figlet
from textual import events
from textual.app import App
from textual.widgets import Header, Footer

@click.group()
def cli():
    title = Figlet(font="slant").renderText("FastAPI Module Manager")
    print(f"[bold green]{title}[/bold green]")
    pass

console = Console(
    theme=Theme(
        {
            "py": "bold cyan",
            "html": "#F49E4C",
            "css": "bold magenta",
            "js": "bold cyan",
            "md": "bold blue",
            "yaml": "bold magenta",
            "toml": "bold red",
            "ini": "#BCB8B1",
            "json": "bold yellow",
            "txt": "bold white",
            "log": "#F5EE9E",
        }
    )
)

@cli.command()
def info():

    def read_dir(path: Path) -> dict:
        buffer_folders: list[tuple[Path, int]] = []
        files_list = {}
        try:
            for idx, i in enumerate(os.listdir(path)):
                if i.startswith(".") or i.startswith("__") or i == Path(__file__).name:
                    continue
                if (path / i).is_dir():
                    buffer_folders.append(
                        (path / i, idx)
                    )
                else:
                    if not files_list.get(path.name):
                        files_list[path.name] = []
                    files_list[path.name].append(i)
            
            for folder in buffer_folders:
                files_list[folder[0].name] = read_dir(folder[0])

            return files_list
                
        except Exception as e:
            print(f"[bold red]Error: {e}[/bold red]")
            return []

    base_path = Path(__file__).parent
    tree_files = read_dir(base_path)
    
    project_table = Table(title="Project Structure")
    project_table.add_column("Folder")
    project_table.add_column("Files")

    def get_color(f_name: str):
        f_ext = f_name.split('.')[-1] if "." in f_name else "white"
        return f"[{f_ext}]{f_name}[/{f_ext}]"

    def add_files_to_table(files_list: dict, folder: str = "[bold green]root[/bold green]"):
        for key, value in files_list.items():
            if isinstance(value, dict):
                add_files_to_table(value, f"{folder}/{key}")
            else:
                project_table.add_row(
                    folder, ", ".join(map(get_color, value))
                )

    add_files_to_table(tree_files)

    panel = Panel.fit(
        Padding(
            project_table,
            (1, 10)
        ),
        title="Info", 
        border_style="green"
    )
    console.print(panel)

@cli.command()
def create_model():
    class CreateModelForm(App):
        def on_mount(self):
            self.theme = "nord"
        
        def compose(self):
            yield Header()
            yield Footer()

        def on_key(self, event: events.Key):
            pass
    

    form_app = CreateModelForm()
    form_app.run()


if __name__ == "__main__":
    cli()