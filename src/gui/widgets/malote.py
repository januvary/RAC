#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QLineEdit,
    QMenu,
)
from PySide6.QtCore import Qt, Signal

from src.gui.widgets.buttons import make_button
from src.gui.widgets.labels import HeadingLabel
from src.gui.widgets.toast import show_toast


class MaloteLabel(QWidget):
    malote_changed = Signal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._mw = main_window

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._shortcut_hint = QLabel("")
        self._shortcut_hint.setFixedHeight(28)
        self._shortcut_hint.setFixedWidth(52)
        self._shortcut_hint.setStyleSheet(
            "color: #9CA3AF; font-size: 14px; border: none;"
        )
        layout.addWidget(self._shortcut_hint)

        self._date_label = QLabel()
        self._date_label.setProperty("malotelabel", "true")
        self._date_label.setFixedHeight(28)
        self._date_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._date_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        layout.addWidget(self._date_label)

        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.refresh()

    def mousePressEvent(self, event):
        _show_malote_dialog(self)

    def open_dialog(self):
        _show_malote_dialog(self)

    def refresh(self):
        from src.utils.text_utils import format_malote_date

        malote = self._mw.state.get_active_malote()
        display = format_malote_date(malote) if malote else "Nenhum malote ativo"
        self._date_label.setText(display)

    def set_shortcut_hint_visible(self, show: bool):
        self._shortcut_hint.setText("(Ctrl+D)" if show else "")


def _show_malote_dialog(label: MaloteLabel):
    from datetime import datetime
    from src.utils.text_utils import format_malote_date

    parent = label.window()
    mw = label._mw

    dlg = QDialog(parent)
    dlg.setWindowTitle("Malotes")
    dlg.setMinimumWidth(340)
    dlg.setMinimumHeight(350)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(12)

    layout.addWidget(HeadingLabel("Malotes"))

    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    tree.setRootIsDecorated(True)
    tree.setAnimated(True)

    def _populate_tree():
        tree.clear()
        malotes = mw.db.get_all_malotes()
        active = mw.state.get_active_malote()
        current_year = datetime.now().year
        year_items: dict[int, QTreeWidgetItem] = {}

        for m in malotes:
            try:
                year = datetime.fromisoformat(m.date).year
            except (ValueError, TypeError):
                year = current_year

            is_active = active and active.id == m.id
            display = format_malote_date(m)
            prefix = "\u2713 " if is_active else "    "
            text = f"{prefix}{display}"

            child = QTreeWidgetItem()
            child.setText(0, text)
            child.setData(0, Qt.ItemDataRole.UserRole, m)
            if is_active:
                font = child.font(0)
                font.setBold(True)
                child.setFont(0, font)

            if year < current_year:
                if year not in year_items:
                    year_item = QTreeWidgetItem()
                    year_item.setText(0, str(year))
                    year_item.setChildIndicatorPolicy(
                        QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                    )
                    year_item.setExpanded(False)
                    year_items[year] = year_item
                    tree.addTopLevelItem(year_item)
                year_items[year].addChild(child)
            else:
                tree.addTopLevelItem(child)

    _populate_tree()

    def on_item_clicked(item, _column):
        malote = item.data(0, Qt.ItemDataRole.UserRole)
        if malote:
            current = mw.state.get_active_malote()
            mw.state.set_active_malote(malote)
            dlg.accept()
            label.refresh()
            if not current or current.id != malote.id or current.date != malote.date:
                label.malote_changed.emit()
        else:
            item.setExpanded(not item.isExpanded())

    tree.itemClicked.connect(on_item_clicked)
    tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def _show_tree_menu(pos):
        item = tree.itemAt(pos)
        if not item:
            return
        malote = item.data(0, Qt.ItemDataRole.UserRole)
        if not malote:
            return

        menu = QMenu(tree)
        edit_action = menu.addAction("Editar")
        has_registros = mw.db.get_registros_by_malote(malote.id)
        if not has_registros:
            delete_action = menu.addAction("Excluir")
        else:
            delete_action = None

        action = menu.exec(tree.viewport().mapToGlobal(pos))
        if action == edit_action:
            _show_edit_malote_dialog(label, malote)
            _populate_tree()
        elif action == delete_action and delete_action is not None:
            from src.gui.styles import colors

            confirm_dlg = QDialog(parent)
            confirm_dlg.setWindowTitle("Excluir Malote")
            confirm_dlg.setMinimumWidth(340)
            confirm_layout = QVBoxLayout(confirm_dlg)
            confirm_layout.setSpacing(16)
            confirm_layout.addWidget(HeadingLabel("Excluir Malote"))
            confirm_layout.addSpacing(4)
            msg = QLabel(f"Excluir malote \"{format_malote_date(malote)}\"?")
            msg.setWordWrap(True)
            c = colors()
            msg.setStyleSheet(f"color: {c['text_primary']}; font-size: 13px;")
            confirm_layout.addWidget(msg)
            confirm_btn_row = QHBoxLayout()
            confirm_btn_row.addStretch()
            confirm_cancel = make_button("Cancelar", "flat")
            confirm_cancel.clicked.connect(confirm_dlg.reject)
            confirm_btn_row.addWidget(confirm_cancel)
            confirm_delete_btn = make_button("Excluir", "destructive")
            confirm_delete_btn.clicked.connect(confirm_dlg.accept)
            confirm_btn_row.addWidget(confirm_delete_btn)
            confirm_layout.addLayout(confirm_btn_row)
            if confirm_dlg.exec() != QDialog.DialogCode.Accepted:
                return

            deleted = mw.db.delete_malote(malote.id)
            if deleted:
                current_active = mw.state.get_active_malote()
                if current_active and current_active.id == malote.id:
                    remaining = [m for m in mw.db.get_all_malotes() if m.id != malote.id]
                    mw.state.set_active_malote(remaining[0] if remaining else None)
                label.refresh()
                label.malote_changed.emit()
                _populate_tree()
                show_toast("Malote excluído", "positive", label)
            else:
                show_toast("Malote possui registros e não pode ser excluído", "negative", label)

    tree.customContextMenuRequested.connect(_show_tree_menu)
    layout.addWidget(tree)

    btn_row = QHBoxLayout()
    new_m = make_button("Novo Malote", "flat")

    def _on_new_malote(_):
        _show_new_malote_dialog(label)
        _populate_tree()

    new_m.clicked.connect(_on_new_malote)
    btn_row.addWidget(new_m)
    btn_row.addStretch()
    close_m = make_button("Fechar", "flat")
    close_m.clicked.connect(dlg.reject)
    btn_row.addWidget(close_m)
    layout.addLayout(btn_row)

    dlg.exec()


def _show_new_malote_dialog(label: MaloteLabel):
    from src.utils.text_utils import parse_date, format_malote_date
    from src.utils.error_handler import ErrorHandler, ErrorContext

    parent = label.window()
    mw = label._mw

    dlg = QDialog(parent)
    dlg.setWindowTitle("Novo Malote")
    dlg.setMinimumWidth(340)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(16)

    layout.addWidget(HeadingLabel("Novo Malote"))

    date_input = QLineEdit()
    date_input.setPlaceholderText("dd/mm ou dd/mm/aa")
    layout.addWidget(date_input)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    cancel = make_button("Cancelar", "flat")
    cancel.clicked.connect(dlg.reject)
    btn_row.addWidget(cancel)
    create = make_button("Criar", "primary")

    def do_create():
        iso = parse_date(date_input.text())
        if not iso:
            show_toast("Data inválida", "negative", label)
            return
        try:
            current = mw.state.get_active_malote()
            malote = mw.db.create_malote(iso)
            mw.state.set_active_malote(malote)
            dlg.accept()
            label.refresh()
            if not current or current.id != malote.id or current.date != malote.date:
                label.malote_changed.emit()
            show_toast(
                f"Malote criado: {format_malote_date(malote)}", "positive", label
            )
        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.MALOTE, show_dialog=False)
            show_toast(f"Erro: {e}", "negative", label)

    create.clicked.connect(do_create)
    btn_row.addWidget(create)
    layout.addLayout(btn_row)

    date_input.returnPressed.connect(do_create)
    dlg.exec()


def _show_edit_malote_dialog(label: MaloteLabel, malote):
    from src.utils.text_utils import parse_date, format_malote_date
    from src.utils.error_handler import ErrorHandler, ErrorContext

    parent = label.window()
    mw = label._mw

    dlg = QDialog(parent)
    dlg.setWindowTitle("Editar Malote")
    dlg.setMinimumWidth(340)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(16)

    layout.addWidget(HeadingLabel("Editar Malote"))

    date_input = QLineEdit()
    date_input.setPlaceholderText("dd/mm ou dd/mm/aa")
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(malote.date)
        date_input.setText(dt.strftime("%d/%m/%Y"))
    except (ValueError, TypeError):
        date_input.setText(malote.date or "")
    date_input.selectAll()
    layout.addWidget(date_input)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    cancel = make_button("Cancelar", "flat")
    cancel.clicked.connect(dlg.reject)
    btn_row.addWidget(cancel)
    save = make_button("Salvar", "primary")

    def do_save():
        iso = parse_date(date_input.text())
        if not iso:
            show_toast("Data inválida", "negative", label)
            return
        if iso == malote.date:
            dlg.accept()
            return
        try:
            mw.db.update_malote(malote.id, iso)
            malote.date = iso
            if mw.state.get_active_malote() and mw.state.get_active_malote().id == malote.id:
                mw.state.set_active_malote(malote)
                label.malote_changed.emit()
            label.refresh()
            dlg.accept()
            show_toast("Malote atualizado", "positive", label)
        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.MALOTE, show_dialog=False)
            show_toast(f"Erro: {e}", "negative", label)

    save.clicked.connect(do_save)
    btn_row.addWidget(save)
    layout.addLayout(btn_row)

    date_input.returnPressed.connect(do_save)
    dlg.exec()
