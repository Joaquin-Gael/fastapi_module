import os
import sys
from pathlib import Path

import aiofiles
import rich_click as click
from mako.template import Template
from pyfiglet import Figlet
from rich import print
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from textual import events
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup, VerticalScroll
from textual.theme import Theme as TTheme
from textual.widgets import (
    Button,
    Checkbox,
    Collapsible,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TextArea,
)

MANAGER_PATH = Path(__file__).parent


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
    }
)
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


def read_dir(path: Path, file_ext: str | None = None) -> dict:
    buffer_folders: list[tuple[Path, int]] = []
    files_list = {}
    try:
        for idx, i in enumerate(os.listdir(path)):
            if i.startswith(".") or i.startswith("__") or i == Path(__file__).name:
                continue
            if (path / i).is_dir():
                buffer_folders.append((path / i, idx))
            else:
                if not files_list.get(path.name):
                    files_list[path.name] = []
                if not file_ext:
                    files_list[path.name].append(i)
                else:
                    ext = i.split(".")[-1]
                    if ext == file_ext:
                        files_list[path.name].append(i)
                    else:
                        continue

        for folder in buffer_folders:
            files_list[folder[0].name] = read_dir(folder[0], file_ext)

        return files_list

    except Exception as e:
        print(f"[bold red]Error: {e}[/bold red]")
        return {}


def get_models(
    models_per_dir: dict = {},
    data: dict | None = None,
    father_dir: str | None = None,
):
    try:
        if not data:
            data = read_dir(
                MANAGER_PATH.parent.joinpath("server", "core", "models"), file_ext="py"
            )
        for dir in data.keys():
            files_o_dir = data[dir]
            if isinstance(files_o_dir, dict) and len(files_o_dir.keys()) > 0:
                if not father_dir:
                    get_models(models_per_dir, files_o_dir, dir)
                    continue
                get_models(models_per_dir, data=files_o_dir, father_dir=father_dir)
            elif isinstance(files_o_dir, list) and len(files_o_dir) > 0:
                if not models_per_dir.get(father_dir):
                    models_per_dir.setdefault(father_dir, files_o_dir)
                else:
                    models_per_dir[father_dir].extend(files_o_dir)
        return models_per_dir
    except Exception as e:
        print(f"[bold red]Error: {e}[/bold red]")
        return {}


@cli.command()
def info():
    tree_files: dict = read_dir(MANAGER_PATH.parent)

    project_table = Table(title="Project Structure")
    project_table.add_column("Folder")
    project_table.add_column("Files")

    def get_color(f_name: str):
        f_ext = f_name.split(".")[-1] if "." in f_name else "white"
        return f"[{f_ext}]{f_name}[/{f_ext}]"

    def add_files_to_table(
        files_list: dict, folder: str = "[bold green]root[/bold green]"
    ):
        for key, value in files_list.items():
            if isinstance(value, dict):
                add_files_to_table(value, f"{folder}/{key}")
            else:
                project_table.add_row(folder, ", ".join(map(get_color, value)))

    add_files_to_table(tree_files)

    panel = Panel.fit(
        Padding(project_table, (1, 10)), title="Info", border_style="green"
    )
    console.print(panel)


@cli.command()
def create_model():
    theme_module = TTheme(
        name="module",
        primary="#F97316",
        secondary="#06B6D4",
        accent="#8B5CF6",
        background="#1E1E2E",
        surface="#2D2D3F",
        panel="#383850",
        success="#10B981",
        error="#EF4444",
        warning="#F59E0B",
    )

    class SideBar(VerticalGroup):
        def compose(self) -> ComposeResult:
            yield VerticalScroll(
                *self._build_collapsibles(),
                id="sidebar_scroll",
            )

        def _build_collapsibles(self):
            structure_module: dict = get_models()
            return [
                Collapsible(
                    VerticalGroup(*[Static(f"{subkey}") for subkey in set(value)]),
                    title=f"{key}",
                )
                for key, value in structure_module.items()
            ]

        async def refresh_sidebar(self) -> None:
            scroll = self.query_one("#sidebar_scroll", VerticalScroll)
            await scroll.remove_children()
            for widget in self._build_collapsibles():
                await scroll.mount(widget)

    class FieldRow(VerticalGroup):
        def __init__(self, field_id: int, **kwargs):
            super().__init__(**kwargs)
            self.field_id = field_id

        def compose(self) -> ComposeResult:
            yield HorizontalGroup(
                Input(placeholder="field name", id=f"field_{self.field_id}_name"),
            )
            yield HorizontalGroup(
                Checkbox("nullable", True, id=f"field_{self.field_id}_nullable"),
                Checkbox("primary_key", False, id=f"field_{self.field_id}_primary_key"),
                Checkbox("unique", False, id=f"field_{self.field_id}_unique"),
                Checkbox("index", False, id=f"field_{self.field_id}_index"),
                Input(
                    placeholder="default value",
                    id=f"field_{self.field_id}_default",
                    classes="default_input",
                ),
            )
            yield HorizontalGroup(
                Select(
                    [
                        ("str", "str"),
                        ("int", "int"),
                        ("float", "float"),
                        ("bool", "bool"),
                        ("datetime", "datetime"),
                        ("date", "date"),
                        ("UUID", "UUID"),
                        ("ForeignKey", "ForeignKey"),
                        ("relationship", "relationship"),
                    ],
                    value="str",
                    id=f"field_{self.field_id}_type",
                    allow_blank=False,
                    prompt="Select type",
                ),
                Input(
                    placeholder="max_length",
                    id=f"field_{self.field_id}_max_length",
                    classes="max_length_input",
                ),
                Button(
                    "X",
                    id=f"field_{self.field_id}_remove",
                    variant="error",
                    classes="remove_btn",
                ),
            )

    class Body(HorizontalGroup):
        def on_mount(self):
            self._field_counter = 0

        def compose(self) -> ComposeResult:
            yield SideBar(id="sidebar")
            model_dirs = get_models()
            folder_options = (
                [(d, d) for d in model_dirs.keys()]
                if model_dirs
                else [("base", "base")]
            )
            yield VerticalScroll(
                Input(
                    placeholder="Model name (e.g. User, Product), tip: snake_case",
                    id="model_name_input",
                ),
                Static(id="status_message_fields", content=""),
                HorizontalGroup(
                    VerticalGroup(
                        Select(
                            folder_options,
                            prompt="Select folder",
                            id="folder_selector",
                            allow_blank=False,
                        ),
                        HorizontalGroup(
                            Button("Add Field", id="add_field_btn", variant="primary"),
                            Button("Generate", id="generate_btn", variant="success"),
                            classes="action_buttons",
                        ),
                    ),
                    VerticalGroup(
                        Input(
                            placeholder="New folder name (e.g. Auth, Products), tip: snake_case",
                            id="new_folder_input",
                        ),
                        Static(id="status_message", content=""),
                        Button(
                            "Create Folder", id="create_folder_btn", variant="primary"
                        ),
                    ),
                ),
                VerticalGroup(id="fields_container"),
                id="main_content",
            )

        def _get_next_field_id(self) -> int:
            self._field_counter += 1
            return self._field_counter

        async def on_button_pressed(self, event: Button.Pressed) -> None:
            button_id = event.button.id or ""
            if button_id == "add_field_btn":
                self._add_field()
            elif button_id == "generate_btn":
                await self._generate()
            elif button_id == "create_folder_btn":
                await self._create_folder()
            elif button_id.endswith("_remove"):
                parts = button_id.split("_")
                if len(parts) >= 2:
                    try:
                        fid = int(parts[1])
                        self._remove_field(fid)
                    except ValueError:
                        pass

        def _add_field(self) -> None:
            container = self.query_one("#fields_container", VerticalGroup)
            fid = self._get_next_field_id()
            field_row = FieldRow(fid, classes="field_row", id=f"field_row_{fid}")
            container.mount(field_row)

        def _remove_field(self, field_id: int) -> None:
            try:
                row = self.query_one(f"#field_row_{field_id}")
                row.remove()
            except Exception:
                pass

        async def _create_folder(self) -> None:
            folder_input = self.query_one("#new_folder_input", Input)
            folder_name = folder_input.value.strip()

            if not folder_name:
                return
            if not folder_name.replace("_", "").replace("-", "").isalnum():
                message = self.query_one("#status_message", Static)
                message.content = "[bold red]Error: Folder name must be alphanumeric (underscores and hyphens allowed)[/bold red]"
                return

            new_dir = MANAGER_PATH.parent / "server" / "core" / "models" / folder_name
            if new_dir.exists():
                message = self.query_one("#status_message", Static)
                message.content = (
                    f"[bold yellow]Folder '{folder_name}' already exists[/bold yellow]"
                )
                return
            else:
                message = self.query_one("#status_message", Static)
                new_dir.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(new_dir / "__init__.py", "w") as f:
                    await f.write("#Blank File")
                async with aiofiles.open(new_dir / "blank.py", "w") as f:
                    await f.write(
                        "#Blank File\n delete this file and replace with your model code generated by the manager"
                    )
                message.content = (
                    f"[bold green]Folder '{folder_name}' created![/bold green]"
                )

            folder_selector = self.query_one("#folder_selector", Select)

            model_dirs = get_models()
            all_folders = set(model_dirs.keys())
            all_folders.add(folder_name)

            new_options = [(f, f) for f in sorted(all_folders)]
            folder_selector.set_options(new_options)
            folder_selector.value = folder_name

            try:
                sidebar = self.app.query_one(SideBar)
                await sidebar.refresh_sidebar()
            except Exception:
                pass

            folder_input.value = ""

        def _collect_fields(self) -> dict:
            container = self.query_one("#fields_container", VerticalGroup)
            fields = {}
            for row in container.query(FieldRow):
                fid = row.field_id
                try:
                    name_widget = self.query_one(f"#field_{fid}_name", Input)
                    type_widget = self.query_one(f"#field_{fid}_type", Select)
                    max_len_widget = self.query_one(f"#field_{fid}_max_length", Input)
                    nullable_widget = self.query_one(f"#field_{fid}_nullable", Checkbox)
                    pk_widget = self.query_one(f"#field_{fid}_primary_key", Checkbox)
                    unique_widget = self.query_one(f"#field_{fid}_unique", Checkbox)
                    index_widget = self.query_one(f"#field_{fid}_index", Checkbox)
                    default_widget = self.query_one(f"#field_{fid}_default", Input)
                except Exception:
                    continue

                field_name = name_widget.value.strip()
                if not field_name:
                    continue

                field_data = {}
                field_type = type_widget.value
                if field_type:
                    field_data["type"] = str(field_type)

                if pk_widget.value:
                    field_data["primary_key"] = True
                if nullable_widget.value:
                    field_data["nullable"] = True
                if unique_widget.value:
                    field_data["unique"] = True
                if index_widget.value:
                    field_data["index"] = True

                max_len_val = max_len_widget.value.strip()
                if max_len_val:
                    try:
                        field_data["max_length"] = int(max_len_val)
                    except ValueError:
                        pass

                default_val = default_widget.value.strip()
                if default_val:
                    field_data["default"] = default_val

                fields[field_name] = field_data
            return fields

        async def _generate(self) -> None:
            model_name_widget = self.query_one("#model_name_input", Input)
            message_status = self.query_one("#status_message_fields", Static)
            model_name = model_name_widget.value.strip()
            if not model_name:
                message_status.content = (
                    "[bold red]Error: Model name is required[/bold red]"
                )
                return
            table_name = model_name.lower()
            model_name = model_name.lower().capitalize()
            while True:
                chars = model_name.find("_")
                if chars == -1:
                    break
                model_name = model_name[:chars] + model_name[chars + 1 :].capitalize()
            model_name = model_name.replace("_", " ")

            folder_widget = self.query_one("#folder_selector", Select)
            selected_folder = folder_widget.value
            if not selected_folder:
                message_status.content = (
                    "[bold red]Error: Please select a target folder[/bold red]"
                )
                return

            fields = self._collect_fields()
            if not fields:
                message_status.content = (
                    "[bold red]Error: At least one field is required[/bold red]"
                )
                return

            # Load and render Mako template
            template_path = MANAGER_PATH / "templates" / "model_template.mako"
            if not template_path.exists():
                message_status.content = (
                    f"[bold red]Error: Template not found at {template_path}[/bold red]"
                )
                return

            template = Template(filename=str(template_path))
            rendered_code = template.render(
                model_name=model_name,
                table_name=table_name,
                fields=fields,
            )

            output_dir: Path = MANAGER_PATH.parent.joinpath(
                "server", "core", "models", selected_folder
            )

            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{table_name}.py"
            with open(output_file, "w") as f:
                f.write(rendered_code)

            message_status.content = (
                f"[bold green]Model {model_name} generated successfully[/bold green]"
            )

            try:
                sidebar = self.app.query_one(SideBar)
                await sidebar.refresh_sidebar()
            except Exception:
                pass

    class CreateModelForm(App):
        CSS_PATH = MANAGER_PATH.joinpath("styles", "manager.tcss").as_posix()

        def on_mount(self):
            self.register_theme(theme_module)
            self.theme = "module"

        def compose(self):
            yield Header()
            yield Body(id="main_content_container")
            yield Footer()

        def on_key(self, event: events.Key):
            pass

    form_app = CreateModelForm()
    form_app.run()


def run():
    cli()
