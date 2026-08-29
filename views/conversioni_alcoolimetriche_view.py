import flet as ft

from diluizione_alcolica import (
    acqua_da_aggiungere,
    diluizione_per_massa_finale,
    diluizione_per_volume_finale,
    peso_da_volume_percento,
)

# Gradazioni target usate più spesso in laboratorio: modifica qui se le tue
# preparazioni tipiche chiedono valori diversi.
GRADAZIONI_RAPIDE = ["60", "70", "80", "85", "90"]

# Sopra questa soglia mostriamo solo un avviso "controlla il valore", senza
# bloccare il calcolo: può essere un dato legittimo, ma è anche il tipico
# punto in cui un refuso passa inosservato.
SOGLIA_AVVISO_QUANTITA = 5000


class ConversioniAlcoolimetricheView:
    """Interfaccia reattiva per i calcoli di ``diluizione_alcolica``."""

    METHOD_AVAILABLE = "available"
    METHOD_MASS = "mass"
    METHOD_VOLUME = "volume"

    def __init__(self, page: ft.Page):
        self._page = page
        self._method = self.METHOD_AVAILABLE
        self._start_value = "96,0"
        self._target_value = ""
        self._amount_value = ""
        self._errors = {"start": "", "target": "", "amount": ""}
        self._amount_warning = ""
        self._result: dict | None = None
        self._copy_status = ""
        self._numeric_filter = ft.InputFilter(regex_string=r"[0-9,.]", allow=True)

    @ft.component
    def build(self) -> ft.Control:
        return ft.Column(
            controls=[
                self._build_header(),
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(content=self._build_input_panel(), col={"xs": 12, "md": 6}),
                        ft.Container(content=self._build_result_card(), col={"xs": 12, "md": 6}),
                    ],
                    spacing=20,
                    run_spacing=20,
                ),
                self._build_method_note(),
            ],
            spacing=20,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def _build_header(self) -> ft.Control:
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=ft.BorderRadius.all(16),
            padding=24,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SCIENCE, size=34, color=ft.Colors.PRIMARY, semantics_label="Laboratorio"),
                    ft.Column(
                        controls=[
                            ft.Text("Conversioni alcoolimetriche", size=26, weight=ft.FontWeight.W_700),
                            ft.Text("Calcolo della diluizione dell'alcool etilico per preparazioni galeniche"),
                        ],
                        spacing=4,
                    ),
                    ft.Row(
                        controls=[self._badge("20 °C"), self._badge("Metodo ponderale")],
                        spacing=8,
                        wrap=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                run_spacing=12,
            ),
        )

    def _badge(self, text: str) -> ft.Control:
        return ft.Container(
            content=ft.Text(text, size=12, weight=ft.FontWeight.W_500),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=ft.BorderRadius.all(20),
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        )

    def _build_input_panel(self) -> ft.Control:
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=ft.BorderRadius.all(16),
            padding=24,
            content=ft.Column(
                controls=[
                    ft.Text("Metodo di preparazione", size=18, weight=ft.FontWeight.W_700),
                    ft.SegmentedButton(
                        segments=[
                            ft.Segment(value=self.METHOD_AVAILABLE, icon=ft.Icons.SCIENCE, label="Da alcool disponibile"),
                            ft.Segment(value=self.METHOD_MASS, icon=ft.Icons.SCALE, label="Per massa finale"),
                            ft.Segment(value=self.METHOD_VOLUME, icon=ft.Icons.STRAIGHTEN, label="Per volume finale"),
                        ],
                        selected=[self._method],
                        on_change=self._cambia_metodo,
                    ),
                    ft.Text("Dati di preparazione", size=18, weight=ft.FontWeight.W_700),
                    self._field("Gradazione alcool di partenza", "° V/V", self._start_value, "start"),
                    self._field(
                        "Gradazione desiderata",
                        "° V/V",
                        self._target_value,
                        "target",
                        "es. 70",
                        on_submit=self._calcola,
                    ),
                    self._build_quick_degree_chips(),
                    self._build_amount_input(),
                    ft.Row(
                        controls=[
                            ft.Button(content="Nuovo calcolo", icon=ft.Icons.REFRESH, on_click=self._reset),
                            ft.Button(
                                content="Calcola diluizione",
                                icon=ft.Icons.CALCULATE,
                                bgcolor=ft.Colors.PRIMARY,
                                color=ft.Colors.ON_PRIMARY,
                                on_click=self._calcola,
                            ),
                        ],
                        spacing=12,
                        wrap=True,
                    ),
                ],
                spacing=16,
            ),
        )

    def _build_quick_degree_chips(self) -> ft.Control:
        return ft.Row(
            controls=[
                ft.Chip(
                    label=f"{grado}°",
                    selected=self._target_value == grado.replace(".", ","),
                    on_click=lambda event, grado=grado: self._imposta_grado_rapido(grado),
                )
                for grado in GRADAZIONI_RAPIDE
            ],
            spacing=6,
            wrap=True,
        )

    def _imposta_grado_rapido(self, grado: str) -> None:
        self._target_value = grado
        self._errors["target"] = ""
        self._render()

    def _field(
        self,
        label: str,
        unit: str,
        value: str,
        key: str,
        hint: str | None = None,
        on_submit=None,
    ) -> ft.Control:
        labels = [ft.Text(label, weight=ft.FontWeight.W_500), ft.Text(unit, color=ft.Colors.ON_SURFACE_VARIANT)]
        if hint:
            labels.append(ft.Text(hint, color=ft.Colors.ON_SURFACE_VARIANT, size=12))
        return ft.Column(
            controls=[
                ft.Row(controls=labels, spacing=8, wrap=True),
                ft.TextField(
                    value=value,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    input_filter=self._numeric_filter,
                    on_change=lambda event, field_key=key: self._salva_valore(field_key, event),
                    on_submit=on_submit,
                ),
                ft.Text(self._errors[key], size=12, color=ft.Colors.ERROR),
            ],
            spacing=4,
        )

    def _build_amount_input(self) -> ft.Control:
        labels = {
            self.METHOD_AVAILABLE: ("Volume alcool di partenza", "mL"),
            self.METHOD_MASS: ("Massa finale desiderata", "g"),
            self.METHOD_VOLUME: ("Volume finale desiderato", "mL"),
        }
        label, unit = labels[self._method]
        return ft.Column(
            controls=[
                self._field(label, unit, self._amount_value, "amount", on_submit=self._calcola),
                ft.Text(self._amount_warning, size=12, color=ft.Colors.ON_SURFACE_VARIANT)
                if self._amount_warning
                else ft.Container(),
            ],
            spacing=2,
        )

    def _build_result_card(self) -> ft.Control:
        if self._result is None:
            return self._result_container(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.ON_SURFACE_VARIANT, size=30),
                    ft.Text("Risultato della diluizione", size=20, weight=ft.FontWeight.W_700),
                    ft.Text("Inserisci i dati della preparazione e premi Calcola diluizione."),
                ]
            )

        if self._method == self.METHOD_AVAILABLE:
            primary = ("Acqua da aggiungere", self._result["acqua_da_aggiungere_ml"], "mL")
            secondary = [
                ("In peso", self._result["acqua_da_aggiungere_g"], "g"),
                ("Volume finale previsto", self._result["volume_finale_ml"], "mL"),
            ]
        elif self._method == self.METHOD_MASS:
            primary = ("Alcool di partenza", self._result["massa_alcol_partenza_g"], "g")
            secondary = [
                ("Acqua depurata", self._result["massa_acqua_g"], "g"),
                ("Massa finale", self._result["massa_finale_g"], "g"),
            ]
        else:
            primary = ("Alcool di partenza", self._result["volume_alcol_partenza_ml"], "mL")
            secondary = [
                ("Acqua da aggiungere", self._result["acqua_da_aggiungere_ml"], "mL"),
                ("Massa acqua", self._result["acqua_da_aggiungere_g"], "g"),
                ("Volume finale", self._result["volume_finale_ml"], "mL"),
            ]

        return self._result_container(
            [
                ft.Text("Risultato della diluizione", size=20, weight=ft.FontWeight.W_700),
                ft.Text(primary[0], color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(
                    f"{self._number(primary[1])} {primary[2]}",
                    size=36,
                    weight=ft.FontWeight.W_700,
                    color=ft.Colors.TEAL_700,
                ),
                ft.Column(controls=[self._metric(label, value, unit) for label, value, unit in secondary], spacing=10),
                self._build_details_card(),
                ft.Button(content="Copia risultato", icon=ft.Icons.COPY, on_click=self._copia_risultato),
                ft.Text(self._copy_status, size=12, color=ft.Colors.TEAL_700),
            ]
        )

    def _result_container(self, controls: list[ft.Control]) -> ft.Control:
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=ft.BorderRadius.all(16),
            padding=24,
            content=ft.Column(controls=controls, spacing=16),
        )

    def _metric(self, label: str, value: float, unit: str) -> ft.Control:
        return ft.Row(
            controls=[ft.Text(label), ft.Text(f"{self._number(value)} {unit}", weight=ft.FontWeight.W_700)],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            wrap=True,
        )

    def _build_details_card(self) -> ft.Control:
        result = self._result or {}
        rows = [
            self._detail("Gradazione iniziale", f"{self._number(result['grado_partenza_vv'])} °V/V"),
            self._detail("Gradazione target", f"{self._number(result['grado_target_vv'])} °V/V"),
        ]
        if "percento_m_m_partenza" in result:
            start_mm = result["percento_m_m_partenza"]
            target_mm = result["percento_m_m_target"]
        else:
            start_mm = peso_da_volume_percento(result["grado_partenza_vv"])
            target_mm = peso_da_volume_percento(result["grado_target_vv"])
        rows.extend(
            [
                self._detail("Equivalente iniziale", f"{self._number(start_mm)} % m/m"),
                self._detail("Equivalente target", f"{self._number(target_mm)} % m/m"),
            ]
        )
        if "massa_finale_g" in result:
            rows.append(self._detail("Massa finale calcolata", f"{self._number(result['massa_finale_g'])} g"))
        return ft.ExpansionTile(
            title=ft.Text("Dettagli del calcolo", weight=ft.FontWeight.W_600),
            leading=ft.Icon(ft.Icons.INFO_OUTLINE),
            controls=rows,
            controls_padding=ft.Padding.only(left=16, right=16, bottom=12),
        )

    def _detail(self, label: str, value: str) -> ft.Control:
        return ft.Row(
            controls=[ft.Text(label, color=ft.Colors.ON_SURFACE_VARIANT), ft.Text(value, weight=ft.FontWeight.W_500)],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            wrap=True,
        )

    def _build_method_note(self) -> ft.Control:
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=ft.BorderRadius.all(16),
            padding=20,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.PRIMARY),
                    ft.Column(
                        controls=[
                            ft.Text("Metodo di calcolo", weight=ft.FontWeight.W_700),
                            ft.Text(
                                "Il calcolo lavora sempre per pesata (il peso si conserva quando si aggiunge "
                                "acqua, il volume no) usando la conversione % V/V ↔ % m/m dalla tabella di "
                                "densità della miscela etanolo-acqua a 20 °C (Perry's Chemical Engineers' "
                                "Handbook), verificata numericamente equivalente alle tavole alcolometriche "
                                "ufficiali FU XII (pagg. 747-757)."
                            ),
                            ft.Text(
                                "Precisione: scarto tipico in quarta cifra decimale rispetto ai valori FU "
                                "ufficiali — adeguata all'uso di laboratorio galenico.",
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=6,
                        expand=True
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    def _salva_valore(self, key: str, event) -> None:
        setattr(self, f"_{key}_value", event.control.value)
        if key == "amount":
            self._aggiorna_avviso_quantita(event.control.value)

    def _aggiorna_avviso_quantita(self, raw_value: str) -> None:
        value = self._parse_value(raw_value, "amount", "Il valore") if raw_value.strip() else None
        if value is not None and value > SOGLIA_AVVISO_QUANTITA:
            self._amount_warning = "Valore insolitamente alto: controlla di non aver digitato uno zero di troppo."
        else:
            self._amount_warning = ""
        self._errors["amount"] = ""
        self._render()

    def _cambia_metodo(self, event) -> None:
        self._method = event.data[0]
        self._amount_value = ""
        self._amount_warning = ""
        self._errors["amount"] = ""
        self._result = None
        self._copy_status = ""
        self._render()

    def _calcola(self, _event) -> None:
        values = self._valida_input()
        if values is None:
            self._render()
            return

        start, target, amount = values
        try:
            if self._method == self.METHOD_AVAILABLE:
                self._result = acqua_da_aggiungere(amount, target, start).__dict__.copy()
            elif self._method == self.METHOD_MASS:
                self._result = diluizione_per_massa_finale(amount, target, start)
            else:
                self._result = diluizione_per_volume_finale(amount, target, start)
                self._result.update(grado_partenza_vv=start, grado_target_vv=target)
        except ValueError as error:
            self._errors["target"] = str(error)
            self._render()
            return

        self._copy_status = ""
        self._render()

    def _valida_input(self) -> tuple[float, float, float] | None:
        self._errors = {"start": "", "target": "", "amount": ""}
        start = self._parse_value(self._start_value, "start", "La gradazione di partenza")
        target = self._parse_value(self._target_value, "target", "La gradazione desiderata")
        amount = self._parse_value(self._amount_value, "amount", "Il valore richiesto")

        if start is not None and not 0 <= start <= 100:
            self._errors["start"] = "Inserisci una gradazione compresa tra 0 e 100."
        if target is not None and not 0 <= target <= 100:
            self._errors["target"] = "Inserisci una gradazione compresa tra 0 e 100."
        if amount is not None and amount <= 0:
            self._errors["amount"] = "Il valore deve essere maggiore di zero."
        if start is not None and target is not None and target >= start:
            self._errors["target"] = "Il grado target deve essere inferiore al grado di partenza."

        if any(self._errors.values()):
            return None
        return start, target, amount

    def _parse_value(self, raw_value: str, key: str, label: str) -> float | None:
        value_text = raw_value.strip().replace(",", ".")
        if not value_text:
            self._errors[key] = f"{label} è obbligatorio."
            return None
        try:
            return float(value_text)
        except ValueError:
            self._errors[key] = f"{label} deve essere un numero valido."
            return None

    def _reset(self, _event) -> None:
        self._start_value = "96,0"
        self._target_value = ""
        self._amount_value = ""
        self._amount_warning = ""
        self._errors = {"start": "", "target": "", "amount": ""}
        self._result = None
        self._copy_status = ""
        self._render()

    async def _copia_risultato(self, _event) -> None:
        if self._result is None:
            return
        start = self._number(self._result["grado_partenza_vv"])
        target = self._number(self._result["grado_target_vv"])
        if self._method == self.METHOD_AVAILABLE:
            text = (
                "Diluizione alcoolimetrica\n"
                f"Alcool di partenza: {self._number(self._result['volume_alcol_partenza_ml'])} mL a {start}° V/V\n"
                f"Gradazione target: {target}° V/V\n"
                f"Acqua da aggiungere: {self._number(self._result['acqua_da_aggiungere_ml'])} mL ({self._number(self._result['acqua_da_aggiungere_g'])} g)\n"
                f"Volume finale: {self._number(self._result['volume_finale_ml'])} mL"
            )
        elif self._method == self.METHOD_MASS:
            text = (
                "Diluizione alcoolimetrica\n"
                f"Alcool di partenza: {self._number(self._result['massa_alcol_partenza_g'])} g a {start}° V/V\n"
                f"Acqua depurata: {self._number(self._result['massa_acqua_g'])} g\n"
                f"Massa finale: {self._number(self._result['massa_finale_g'])} g a {target}° V/V"
            )
        else:
            text = (
                "Diluizione alcoolimetrica\n"
                f"Alcool di partenza: {self._number(self._result['volume_alcol_partenza_ml'])} mL a {start}° V/V\n"
                f"Acqua da aggiungere: {self._number(self._result['acqua_da_aggiungere_ml'])} mL ({self._number(self._result['acqua_da_aggiungere_g'])} g)\n"
                f"Volume finale: {self._number(self._result['volume_finale_ml'])} mL a {target}° V/V"
            )
        await self._page.clipboard.set(text)
        self._copy_status = "Risultato copiato negli appunti."
        self._render()

    def _render(self) -> None:
        self._page.render(self.build)

    @staticmethod
    def _number(value: float) -> str:
        return f"{value:.2f}".replace(".", ",")