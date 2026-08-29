import flet as ft

from views.conversioni_alcoolimetriche_view import ConversioniAlcoolimetricheView


def main(page: ft.Page) -> None:
    page.title = "Conversioni alcoolimetriche"
    page.padding = 24
    page.bgcolor = ft.Colors.SURFACE

    view = ConversioniAlcoolimetricheView(page)
    page.render(view.build)


ft.run(main)
