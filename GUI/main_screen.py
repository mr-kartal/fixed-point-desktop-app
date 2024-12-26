from copy import deepcopy
import flet
from flet import (AppBar, Colors, ElevatedButton, Card,Page, Column, Row, Container, Text, FilePicker, Icons, IconButton, SnackBar,
                  DataTable, DataColumn, DataCell, DataRow, NavigationRail, NavigationRailDestination,Stack,VerticalDivider,colors,icons)
from flet.utils import slugify
import json


class ResponsiveMenuLayout(Row):
    def __init__(
        self,
        page,
        pages,
        *args,
        support_routes=True,
        menu_extended=True,
        minimize_to_icons=False,
        landscape_minimize_to_icons=False,
        portrait_minimize_to_icons=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.page = page
        self.pages = pages

        self._minimize_to_icons = minimize_to_icons
        self._landscape_minimize_to_icons = landscape_minimize_to_icons
        self._portrait_minimize_to_icons = portrait_minimize_to_icons
        self._support_routes = support_routes

        self.expand = True

        self.navigation_items = [navigation_item for navigation_item, _ in pages]
        self.routes = [
            f"/{item.pop('route', None) or slugify(item['label'])}"
            for item in self.navigation_items
        ]
        self.navigation_rail = self.build_navigation_rail()
        self.update_destinations()
        self._menu_extended = menu_extended
        self.navigation_rail.extended = menu_extended

        page_contents = [page_content for _, page_content in pages]

        self.menu_panel = Row(
            controls=[self.navigation_rail, VerticalDivider(width=1)],
            spacing=0,
            tight=True,
        )
        self.content_area = Column(page_contents, expand=True)

        self._was_portrait = self.is_portrait()
        self._panel_visible = self.is_landscape()

        self.set_navigation_content()

        if support_routes:
            self._route_change(page.route)
            self.page.on_route_change = self._on_route_change
        self._change_displayed_page()

        self.page.on_resized = self.handle_resize

    def select_page(self, page_number):
        self.navigation_rail.selected_index = page_number
        self._change_displayed_page()

    @property
    def minimize_to_icons(self) -> bool:
        return self._minimize_to_icons or (
            self._landscape_minimize_to_icons and self._portrait_minimize_to_icons
        )

    @minimize_to_icons.setter
    def minimize_to_icons(self, value: bool):
        self._minimize_to_icons = value
        self.set_navigation_content()

    @property
    def landscape_minimize_to_icons(self) -> bool:
        return self._landscape_minimize_to_icons or self._minimize_to_icons

    @landscape_minimize_to_icons.setter
    def landscape_minimize_to_icons(self, value: bool):
        self._landscape_minimize_to_icons = value
        self.set_navigation_content()

    @property
    def portrait_minimize_to_icons(self) -> bool:
        return self._portrait_minimize_to_icons or self._minimize_to_icons

    @portrait_minimize_to_icons.setter
    def portrait_minimize_to_icons(self, value: bool):
        self._portrait_minimize_to_icons = value
        self.set_navigation_content()

    @property
    def menu_extended(self) -> bool:
        return self._menu_extended

    @menu_extended.setter
    def menu_extended(self, value: bool):
        self._menu_extended = value

        dimension_minimized = (
            self.landscape_minimize_to_icons
            if self.is_landscape()
            else self.portrait_minimize_to_icons
        )
        if not dimension_minimized or self._panel_visible:
            self.navigation_rail.extended = value

    def _navigation_change(self, e):
        self._change_displayed_page()
        self.check_toggle_on_select()
        self.page.update()

    def _change_displayed_page(self):
        page_number = self.navigation_rail.selected_index
        if self._support_routes:
            self.page.route = self.routes[page_number]
        for i, content_page in enumerate(self.content_area.controls):
            content_page.visible = page_number == i

    def _route_change(self, route):
        try:
            page_number = self.routes.index(route)
        except ValueError:
            page_number = 0

        self.select_page(page_number)

    def _on_route_change(self, event):
        self._route_change(event.route)
        self.page.update()

    def build_navigation_rail(self):
        return NavigationRail(
            selected_index=0,
            label_type="none",
            on_change=self._navigation_change,
        )

    def update_destinations(self, icons_only=False):
        navigation_items = self.navigation_items
        if icons_only:
            navigation_items = deepcopy(navigation_items)
            for item in navigation_items:
                item.pop("label")

        self.navigation_rail.destinations = [
            NavigationRailDestination(**nav_specs) for nav_specs in navigation_items
        ]
        self.navigation_rail.label_type = "none" if icons_only else "all"

    def handle_resize(self, e):
        if self._was_portrait != self.is_portrait():
            self._was_portrait = self.is_portrait()
            self._panel_visible = self.is_landscape()
            self.set_navigation_content()
            self.page.update()

    def toggle_navigation(self, event=None):
        self._panel_visible = not self._panel_visible
        self.set_navigation_content()
        self.page.update()

    def check_toggle_on_select(self):
        if self.is_portrait() and self._panel_visible:
            self.toggle_navigation()

    def set_navigation_content(self):
        if self.is_landscape():
            self.add_landscape_content()
        else:
            self.add_portrait_content()

    def add_landscape_content(self):
        self.controls = [self.menu_panel, self.content_area]
        if self.landscape_minimize_to_icons:
            self.update_destinations(icons_only=not self._panel_visible)
            self.menu_panel.visible = True
            if not self._panel_visible:
                self.navigation_rail.extended = False
            else:
                self.navigation_rail.extended = self.menu_extended
        else:
            self.update_destinations()
            self.navigation_rail.extended = self._menu_extended
            self.menu_panel.visible = self._panel_visible

    def add_portrait_content(self):
        if self.portrait_minimize_to_icons and not self._panel_visible:
            self.controls = [self.menu_panel, self.content_area]
            self.update_destinations(icons_only=True)
            self.menu_panel.visible = True
            self.navigation_rail.extended = False
        else:
            if self._panel_visible:
                dismiss_shield = Container(
                    expand=True,
                    on_click=self.toggle_navigation,
                )
                self.controls = [
                    Stack(
                        controls=[self.content_area, dismiss_shield, self.menu_panel],
                        expand=True,
                    )
                ]
            else:
                self.controls = [
                    Stack(controls=[self.content_area, self.menu_panel], expand=True)
                ]
            self.update_destinations()
            self.navigation_rail.extended = self.menu_extended
            self.menu_panel.visible = self._panel_visible

    def is_portrait(self) -> bool:
        # Return true if window/display is narrow
        # return self.page.window_height >= self.page.window_width
        return self.page.height >= self.page.width

    def is_landscape(self) -> bool:
        # Return true if window/display is wide
        return self.page.width > self.page.height


if __name__ == "__main__":

    def main(page: Page, title="Fixed-Point Iteration Method"):
        page.title = title
        menu_button = IconButton(Icons.MENU)
        page.appbar = AppBar(
            leading=menu_button,
            leading_width=40,
            bgcolor=Colors.TEAL,
        )

        # JSON Input Section
        json_file_picker = FilePicker(on_result=lambda e: handle_json_file(e, page))
        page.overlay.append(json_file_picker)

        json_input_button = ElevatedButton(
            "Select JSON Input File",
            icon=Icons.UPLOAD_FILE,
            on_click=lambda e: json_file_picker.pick_files()
        )

        json_feedback = Text(value="", size=14, color="green")

        def handle_json_file(e, page):
            if not e.files:
                json_feedback.value = "No file selected."
                page.update()
                return

            try:
                with open(e.files[0].path, "r") as f:
                    input_data = json.load(f)

                validate_json_input(input_data)

                json_feedback.value = f"Loaded JSON file: {e.files[0].name}"
                page.overlay.append(SnackBar(Text("File loaded successfully!"), open=True))
                # Process input_data as needed
            except Exception as ex:
                json_feedback.value = f"Error: {str(ex)}"
                page.overlay.append(SnackBar(Text("Failed to load file."), open=True))
            finally:
                page.update()

        def validate_json_input(data):
            required_keys = {"function", "initial_guess", "tolerance", "max_iterations"}
            if not all(key in data for key in required_keys):
                raise ValueError(f"Missing keys in JSON file. Required keys: {', '.join(required_keys)}")

        #Calculate Button
        calculate_button = ElevatedButton(
            "Calculate",
            icon=Icons.CALCULATE_OUTLINED,
            on_click= None
        )

        pages = [
            (
                dict(
                    icon=Icons.INPUT_OUTLINED,
                    selected_icon=Icons.INPUT,
                    label="Input",
                ),
                create_page(
                    title="Input",
                    body="Upload JSON file",
                    controls=
                    Column([
                                    Container(content=json_input_button, padding=10),
                                    Container(content=json_feedback, padding=10),
                                    Container(content=calculate_button, padding=10), #add if only json feedback is positive
                                    Text("Results:", size=18, weight="bold"),]), # add if calculation is successful
                ),
            ),
            (
                dict(
                    icon=Icons.AUTO_GRAPH_OUTLINED,
                    selected_icon=Icons.AUTO_GRAPH,
                    label="Animation",
                ),
                create_page(
                    title="Animation",
                ),
            ),
            (
                dict(
                    icon=Icons.OUTPUT_OUTLINED,
                    selected_icon=Icons.OUTPUT,
                    label="Output",
                ),
                create_page(
                    title="Output",
                    body="Export JSON file"

                ),
            ),
            (
                dict(
                    icon=Icons.PEOPLE_OUTLINE,
                    selected_icon=Icons.PEOPLE,
                    label="Team",
                ),
                create_page(
                    title="Developer Team",
                    body=
                    "Çağrı KARTAL - 200315053" "\n"
                    "Eren ATASUN" "\n"
                    "Eren AYDOĞDU" "\n"

                ),
            ),
            (
                dict(
                    icon=Icons.INFO_OUTLINE,
                    selected_icon=Icons.INFO,
                    label="Info",
                ),
                create_page(
                    "Read Me",
                    "Inputs:" "\n"
                    "- f(x): The function to find its root"  "\n"
                    "- x_0: The initial guess for iterative process" "\n"
                    "- tol: A value, which is very close to zero, to stop the iterations" "\n"
                    "- max_iter: The maximum number of iterations" "\n" "\n"
                    "Outputs:" "\n"

                ),
            ),
        ]

        menu_layout = ResponsiveMenuLayout(page, pages)
        page.add(menu_layout)
        menu_button.on_click = lambda e: menu_layout.toggle_navigation()

    def create_page(title: str = None , body: str = None, controls: flet.Control = None):
        return Row(
            controls=[
                Column(
                    horizontal_alignment="stretch",
                    controls=[
                        Card(content=Container(Text(title, weight="bold"), padding=8)),
                        Text(body),
                        controls or Container()
                    ],
                    expand=True,
                ),
            ],
            expand=True,
        )

    def toggle_icons_only(menu: ResponsiveMenuLayout):
        menu.minimize_to_icons = not menu.minimize_to_icons
        menu.page.update()

    def toggle_menu_width(menu: ResponsiveMenuLayout):
        menu.menu_extended = not menu.menu_extended
        menu.page.update()

    flet.app(target=main)