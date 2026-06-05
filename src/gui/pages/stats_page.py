#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
    QHeaderView,
    QDialog,
    QTreeWidgetItem,
)
from datetime import datetime

from PySide6.QtCore import Qt

from src.gui.widgets import (
    SectionLabel,
    make_button,
    BasePage,
)
from src.gui.widgets.labels import HeadingLabel
from src.gui.widgets._malote_tree import (
    make_malote_tree,
    populate_malote_tree,
    wire_tree_keyboard,
)
from src.gui.constants import TIPO_LABELS
from src.gui.styles import colors

_CANCELLED = object()


class _TipoCard(QWidget):
    def __init__(self, tipo_key: str, value: str):
        super().__init__()
        c = colors()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            f"QWidget {{ background: transparent; border: 1px solid {c['border_light']}; "
            f"border-radius: 6px; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._value_label = QLabel(value)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_label.setStyleSheet(
            f"font-size: 24px; font-weight: 700; color: {c['text_primary']}; border: none;"
        )
        layout.addWidget(self._value_label)

        tipo_label = TIPO_LABELS.get(tipo_key, tipo_key)
        lbl = QLabel(tipo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_secondary']}; border: none;"
        )
        layout.addWidget(lbl)

    def set_value(self, value: str):
        self._value_label.setText(value)


class StatsPage(BasePage):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._date_from: str | None = None
        self._date_to: str | None = None
        self._build_ui()
        self._load_stats()

    def _build_ui(self):
        layout = self._scaffold()
        self._build_header(layout)
        layout.addSpacing(16)

        self._build_tipo_cards(layout)
        layout.addSpacing(10)

        self._build_medications_table(layout)

    def _build_header(self, layout: QVBoxLayout):
        h = self._add_back_button(layout)

        row = QHBoxLayout()
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.setSpacing(0)

        self._from_btn = make_button("Inicio", "flat")
        self._from_btn.setFixedWidth(115)
        self._from_btn.clicked.connect(lambda: self._pick_date("from"))
        row.addWidget(self._from_btn)

        row.addSpacing(20)

        c = colors()
        sep = QLabel("\u2192")
        sep.setStyleSheet(f"color: {c['text_secondary']}; border: none;")
        row.addWidget(sep)

        row.addSpacing(20)

        self._to_btn = make_button("Fim", "flat")
        self._to_btn.setFixedWidth(115)
        self._to_btn.clicked.connect(lambda: self._pick_date("to"))
        row.addWidget(self._to_btn)

        layout.addLayout(row)

    def _pick_date(self, side: str):
        result = _show_date_picker(self, side)
        if result is _CANCELLED:
            return
        if side == "from":
            self._date_from = result
            if self._date_to and self._date_from and self._date_from > self._date_to:
                self._date_to = self._date_from
        else:
            self._date_to = result
            if self._date_from and self._date_to and self._date_from > self._date_to:
                self._date_from = self._date_to
        self._update_date_buttons()
        self._load_stats()

    def _update_date_buttons(self):
        self._from_btn.setText(
            datetime.fromisoformat(self._date_from).strftime("%d/%m/%Y")
            if self._date_from else "Inicio"
        )
        self._to_btn.setText(
            datetime.fromisoformat(self._date_to).strftime("%d/%m/%Y")
            if self._date_to else "Fim"
        )

    def _build_tipo_cards(self, layout: QVBoxLayout):
        row = QHBoxLayout()
        row.setSpacing(16)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tipo_cards: dict[str, _TipoCard] = {}
        for tipo_key in TIPO_LABELS:
            card = _TipoCard(tipo_key, "0")
            card.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            self._tipo_cards[tipo_key] = card
            row.addWidget(card)
        layout.addLayout(row)

    def _build_medications_table(self, layout: QVBoxLayout):
        layout.addWidget(SectionLabel("Medicamentos"))
        layout.addSpacing(8)

        self._meds_table = QTableWidget(0, 2)
        self._meds_table.setHorizontalHeaderLabels(["Medicamento", "Registros"])
        self._meds_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._meds_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self._meds_table.horizontalHeader().resizeSection(1, 80)
        self._meds_table.horizontalHeader().setFixedHeight(28)
        self._meds_table.verticalHeader().setVisible(False)
        self._meds_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._meds_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._meds_table.setAlternatingRowColors(True)
        self._meds_table.verticalHeader().setDefaultSectionSize(32)
        self._meds_table.setMinimumHeight(28 + 32 * 6)
        self._style_table(self._meds_table)
        layout.addWidget(self._meds_table)

    def _load_stats(self):
        db = self._mw.db

        tipo_rows = db.get_stats_by_tipo(
            date_from=self._date_from, date_to=self._date_to
        )
        tipo_map = {r["tipo"]: r for r in tipo_rows}
        for tipo_key in TIPO_LABELS:
            r = tipo_map.get(tipo_key)
            self._tipo_cards[tipo_key].set_value(str(r["registros"]) if r else "0")

        meds = db.get_stats_top_medications(
            date_from=self._date_from, date_to=self._date_to
        )
        self._fill_meds_table(meds)

    def _fill_meds_table(self, rows: list[dict]):
        self._meds_table.setRowCount(0)
        for r in rows:
            row = self._meds_table.rowCount()
            self._meds_table.insertRow(row)
            self._meds_table.setItem(row, 0, self._cell(r["medicamento"]))
            self._meds_table.setItem(
                row, 1, self._cell(str(r["registros"]), center=True)
            )

    @staticmethod
    def _cell(text: str, center: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    @staticmethod
    def _style_table(table: QTableWidget) -> None:
        c = colors()
        table.setStyleSheet(
            f"""
            QTableWidget {{
                border: 1px solid {c['border_light']};
                border-radius: 6px;
                background: transparent;
                alternate-background-color: {c['table_alt_bg']};
                gridline-color: {c['gridline']};
                font-size: 13px;
                color: {c['text_primary']};
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {c['gridline']};
                color: {c['text_primary']};
            }}
            QHeaderView::section {{
                background: {c['bg_card_alt']};
                color: {c['text_secondary']};
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
                border: none;
                border-bottom: 1px solid {c['border_light']};
            }}
        """
        )


_RESET_SENTINEL = object()


def _show_date_picker(parent_page: StatsPage, side: str) -> str | None:
    mw = parent_page._mw
    parent = parent_page.window()

    reset_label = "Início" if side == "from" else "Fim"

    dlg = QDialog(parent)
    dlg.setWindowTitle("Selecionar Data")
    dlg.setMinimumWidth(320)
    dlg.setMinimumHeight(300)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(12)

    layout.addWidget(HeadingLabel("Selecionar Data"))

    tree = make_malote_tree()

    reset_item = QTreeWidgetItem()
    reset_item.setText(0, reset_label)
    reset_item.setData(0, Qt.ItemDataRole.UserRole, _RESET_SENTINEL)

    malotes = mw.db.get_all_malotes()
    populate_malote_tree(
        tree,
        malotes,
        get_user_data=lambda m, _dt: m.date,
        prepend_items=[reset_item],
    )

    selected_date = [_CANCELLED]

    def on_item_clicked(item, _column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is _RESET_SENTINEL:
            selected_date[0] = None
            dlg.accept()
        elif data is not None:
            selected_date[0] = data
            dlg.accept()
        else:
            item.setExpanded(not item.isExpanded())

    tree.itemClicked.connect(on_item_clicked)
    wire_tree_keyboard(tree, lambda item: on_item_clicked(item, 0))

    layout.addWidget(tree)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    close_btn = make_button("Cancelar", "flat")
    close_btn.setAutoDefault(False)
    close_btn.clicked.connect(dlg.reject)
    btn_row.addWidget(close_btn)
    layout.addLayout(btn_row)

    dlg.exec()
    return selected_date[0]
