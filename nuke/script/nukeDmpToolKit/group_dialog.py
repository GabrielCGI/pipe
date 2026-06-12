"""
group_dialog.py
QDialog pour grouper des layers avant projection sur cards 3D.

Compatible PySide2 (Nuke <= 15) et PySide6 (Nuke >= 16).
Les imports Qt sont differes pour eviter de charger Qt
avant que le QApplication de Nuke soit pret.
"""

import nuke

_USE_PYSIDE6 = nuke.NUKE_VERSION_MAJOR >= 16


def _import_qt():
    """Importe QtWidgets et QtCore depuis le bon PySide."""
    if _USE_PYSIDE6:
        from PySide6 import QtWidgets, QtCore
    else:
        from PySide2 import QtWidgets, QtCore
    return QtWidgets, QtCore


def detect_prefix_groups(layer_names):
    """
    Detecte les groupes de layers par prefixe commun (PREFIX_).

    Retourne list[tuple[str, list[int]]] tries par index min.
    Seuls les prefixes avec 2+ layers sont retenus.
    """
    from collections import defaultdict

    # 1. Extraire les prefixes candidats de chaque layer
    candidates = defaultdict(set)  # prefix -> set of layer indices
    for i, name in enumerate(layer_names):
        pos = 0
        while True:
            pos = name.find("_", pos)
            if pos == -1:
                break
            prefix = name[:pos]
            if prefix:
                candidates[prefix].add(i)
            pos += 1

    # Ajouter les layers dont le nom exact est un prefixe existant
    for i, name in enumerate(layer_names):
        if name in candidates:
            candidates[name].add(i)

    # 2. Filtrer : garder seulement les prefixes avec 2+ matchs
    candidates = {p: indices for p, indices in candidates.items()
                  if len(indices) >= 2}

    if not candidates:
        return []

    # 3. Longest-match : assigner chaque layer au prefixe le plus long
    #    Trier les prefixes du plus long au plus court
    sorted_prefixes = sorted(candidates.keys(), key=len, reverse=True)
    assigned = {}  # layer_index -> prefix
    groups = defaultdict(list)

    for i in range(len(layer_names)):
        for prefix in sorted_prefixes:
            if i in candidates[prefix] and i not in assigned:
                assigned[i] = prefix
                groups[prefix].append(i)
                break

    # 4. Supprimer les groupes tombes sous 2 membres apres reassignation
    groups = {p: indices for p, indices in groups.items()
              if len(indices) >= 2}

    # 5. Trier par index min pour preserver l'ordre du stack
    result = sorted(groups.items(), key=lambda x: min(x[1]))
    return [(prefix, sorted(indices)) for prefix, indices in result]


def show_group_dialog(layer_names, enable_grouping=True, auto_group=True):
    """
    Affiche le dialog de groupage / exclusion modal.

    Retourne (grouping, ignored_indices) ou None si annule.
      grouping : list[tuple[str, list[int]]]
      ignored_indices : list[int]
    """
    QtWidgets, _ = _import_qt()

    pre_groups = None
    if enable_grouping and auto_group:
        pre_groups = detect_prefix_groups(layer_names)

    parent = QtWidgets.QApplication.activeWindow()
    dialog = _build_dialog(layer_names, parent, enable_grouping, pre_groups=pre_groups)

    if _USE_PYSIDE6:
        accepted = dialog.exec()
    else:
        accepted = dialog.exec_()

    if accepted:
        return dialog.get_result()
    return None


def _build_dialog(layer_names, parent, enable_grouping=True, pre_groups=None):
    """Construit le dialog avec le bon PySide."""
    QtWidgets, QtCore = _import_qt()
    Qt = QtCore.Qt

    # Enums compatibles PySide2 / PySide6
    if _USE_PYSIDE6:
        USER_ROLE = Qt.ItemDataRole.UserRole
        ALIGN_TOP = Qt.AlignmentFlag.AlignTop
        MOVE_ACTION = Qt.DropAction.MoveAction
        DRAG_DROP = QtWidgets.QAbstractItemView.DragDropMode.DragDrop
        EXT_SELECT = QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        FRAME_BOX = QtWidgets.QFrame.Shape.Box
        FRAME_PLAIN = QtWidgets.QFrame.Shadow.Plain
        SIZE_EXPAND = QtWidgets.QSizePolicy.Policy.Expanding
        SIZE_MIN = QtWidgets.QSizePolicy.Policy.Minimum
        BTN_OK = QtWidgets.QDialogButtonBox.StandardButton.Ok
        BTN_CANCEL = QtWidgets.QDialogButtonBox.StandardButton.Cancel
    else:
        USER_ROLE = Qt.UserRole
        ALIGN_TOP = Qt.AlignTop
        MOVE_ACTION = Qt.MoveAction
        DRAG_DROP = QtWidgets.QAbstractItemView.DragDrop
        EXT_SELECT = QtWidgets.QAbstractItemView.ExtendedSelection
        FRAME_BOX = QtWidgets.QFrame.Box
        FRAME_PLAIN = QtWidgets.QFrame.Plain
        SIZE_EXPAND = QtWidgets.QSizePolicy.Expanding
        SIZE_MIN = QtWidgets.QSizePolicy.Minimum
        BTN_OK = QtWidgets.QDialogButtonBox.Ok
        BTN_CANCEL = QtWidgets.QDialogButtonBox.Cancel

    # ------------------------------------------------------------------
    #  DropListWidget
    # ------------------------------------------------------------------
    class DropListWidget(QtWidgets.QListWidget):

        def __init__(self, par=None):
            super().__init__(par)
            self.setAcceptDrops(True)
            self.setDragEnabled(True)
            self.setDragDropMode(DRAG_DROP)
            self.setDefaultDropAction(MOVE_ACTION)
            self.setSelectionMode(EXT_SELECT)

        def dragEnterEvent(self, event):
            if event.source() and isinstance(event.source(), QtWidgets.QListWidget):
                event.acceptProposedAction()
            else:
                event.ignore()

        def dragMoveEvent(self, event):
            if event.source() and isinstance(event.source(), QtWidgets.QListWidget):
                event.acceptProposedAction()
            else:
                event.ignore()

        def dropEvent(self, event):
            source = event.source()
            if not source or not isinstance(source, QtWidgets.QListWidget) or source is self:
                event.ignore()
                return

            items_data = []
            for item in source.selectedItems():
                items_data.append((item.text(), item.data(USER_ROLE)))

            for item in reversed(source.selectedItems()):
                source.takeItem(source.row(item))

            for text, idx in items_data:
                new_item = QtWidgets.QListWidgetItem(text)
                new_item.setData(USER_ROLE, idx)
                self.addItem(new_item)

            event.acceptProposedAction()

    # ------------------------------------------------------------------
    #  GroupWidget
    # ------------------------------------------------------------------
    class GroupWidget(QtWidgets.QFrame):

        def __init__(self, name, parent_dialog):
            super().__init__()
            self.parent_dialog = parent_dialog
            self.setFrameStyle(FRAME_BOX | FRAME_PLAIN)
            self.setLineWidth(1)

            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(4, 4, 4, 4)
            layout.setSpacing(4)

            header = QtWidgets.QHBoxLayout()
            self.name_edit = QtWidgets.QLineEdit(name)
            self.name_edit.setStyleSheet("font-weight: bold;")
            header.addWidget(self.name_edit)

            delete_btn = QtWidgets.QPushButton("X")
            delete_btn.setFixedWidth(24)
            delete_btn.clicked.connect(self._on_delete)
            header.addWidget(delete_btn)
            layout.addLayout(header)

            self.layer_list = DropListWidget()
            self.layer_list.setMinimumHeight(40)
            self.layer_list.setSizePolicy(SIZE_EXPAND, SIZE_MIN)
            layout.addWidget(self.layer_list)

        def _on_delete(self):
            self.parent_dialog._return_items_from_group(self)
            self.parent_dialog._remove_group_widget(self)

        def get_indices(self):
            indices = []
            for i in range(self.layer_list.count()):
                item = self.layer_list.item(i)
                indices.append(item.data(USER_ROLE))
            return indices

        def get_name(self):
            return self.name_edit.text().strip() or "Group"

    # ------------------------------------------------------------------
    #  LayerGroupDialog
    # ------------------------------------------------------------------
    class LayerGroupDialog(QtWidgets.QDialog):

        def __init__(self, names, par=None, show_groups=True, pre_groups=None):
            super().__init__(par)
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self._show_groups = show_groups
            title = "Layer Grouping" if show_groups else "Layer Selection"
            self.setWindowTitle(title)
            self.setMinimumSize(600, 400)
            self.resize(700, 500)

            self._group_counter = 0
            self._group_widgets = []

            main_layout = QtWidgets.QVBoxLayout(self)
            columns = QtWidgets.QHBoxLayout()

            # Colonne gauche : layers
            left = QtWidgets.QVBoxLayout()
            left.addWidget(QtWidgets.QLabel("Layers"))
            self.ungrouped_list = DropListWidget()
            for i, name in enumerate(names):
                item = QtWidgets.QListWidgetItem(name)
                item.setData(USER_ROLE, i)
                self.ungrouped_list.addItem(item)
            left.addWidget(self.ungrouped_list)

            ungroup_btn = QtWidgets.QPushButton("<< Ungroup")
            ungroup_btn.clicked.connect(self._ungroup_selected)
            left.addWidget(ungroup_btn)

            columns.addLayout(left, stretch=1)

            # Colonne centrale : groupes (seulement si enable_grouping)
            if show_groups:
                mid = QtWidgets.QVBoxLayout()
                mid.addWidget(QtWidgets.QLabel("Groups"))

                self.scroll_area = QtWidgets.QScrollArea()
                self.scroll_area.setWidgetResizable(True)
                self.scroll_container = QtWidgets.QWidget()
                self.groups_layout = QtWidgets.QVBoxLayout(self.scroll_container)
                self.groups_layout.setAlignment(ALIGN_TOP)
                self.scroll_area.setWidget(self.scroll_container)
                mid.addWidget(self.scroll_area)

                add_group_btn = QtWidgets.QPushButton("+ Group")
                add_group_btn.clicked.connect(self._add_group)
                mid.addWidget(add_group_btn)

                columns.addLayout(mid, stretch=1)

            # Colonne droite : ignored layers
            right = QtWidgets.QVBoxLayout()
            right.addWidget(QtWidgets.QLabel("Ignored Layers"))
            self.ignored_list = DropListWidget()
            self.ignored_list.setStyleSheet(
                "QListWidget { border: 2px solid #664444; background: #1a1111; }")
            right.addWidget(self.ignored_list)
            columns.addLayout(right, stretch=1)

            main_layout.addLayout(columns)

            button_box = QtWidgets.QDialogButtonBox(BTN_OK | BTN_CANCEL)
            button_box.accepted.connect(self.accept)
            button_box.rejected.connect(self.reject)
            main_layout.addWidget(button_box)

            # Pre-peupler les groupes par prefixe
            if pre_groups and show_groups:
                self._populate_pre_groups(pre_groups)

        def _add_group(self):
            self._group_counter += 1
            group = GroupWidget("Group {}".format(self._group_counter), self)
            self._group_widgets.append(group)
            self.groups_layout.addWidget(group)

        def _add_group_named(self, name):
            group = GroupWidget(name, self)
            self._group_widgets.append(group)
            self.groups_layout.addWidget(group)
            return group

        def _populate_pre_groups(self, pre_groups):
            for prefix, indices in pre_groups:
                group = self._add_group_named(prefix)
                idx_set = set(indices)
                rows_to_move = []
                for row in range(self.ungrouped_list.count()):
                    item = self.ungrouped_list.item(row)
                    if item.data(USER_ROLE) in idx_set:
                        rows_to_move.append(row)
                for row in reversed(rows_to_move):
                    item = self.ungrouped_list.takeItem(row)
                    new_item = QtWidgets.QListWidgetItem(item.text())
                    new_item.setData(USER_ROLE, item.data(USER_ROLE))
                    group.layer_list.addItem(new_item)

        def _remove_group_widget(self, group_widget):
            self._group_widgets.remove(group_widget)
            self.groups_layout.removeWidget(group_widget)
            group_widget.deleteLater()

        def _return_items_from_group(self, group_widget):
            lst = group_widget.layer_list
            while lst.count():
                item = lst.takeItem(0)
                new_item = QtWidgets.QListWidgetItem(item.text())
                new_item.setData(USER_ROLE, item.data(USER_ROLE))
                self.ungrouped_list.addItem(new_item)

        def _ungroup_selected(self):
            for group in self._group_widgets:
                selected = list(group.layer_list.selectedItems())
                for item in reversed(selected):
                    idx = item.data(USER_ROLE)
                    text = item.text()
                    group.layer_list.takeItem(group.layer_list.row(item))
                    new_item = QtWidgets.QListWidgetItem(text)
                    new_item.setData(USER_ROLE, idx)
                    self.ungrouped_list.addItem(new_item)

            # Also ungroup from ignored list
            selected = list(self.ignored_list.selectedItems())
            for item in reversed(selected):
                idx = item.data(USER_ROLE)
                text = item.text()
                self.ignored_list.takeItem(self.ignored_list.row(item))
                new_item = QtWidgets.QListWidgetItem(text)
                new_item.setData(USER_ROLE, idx)
                self.ungrouped_list.addItem(new_item)

        def get_result(self):
            grouping = []
            for group in self._group_widgets:
                indices = group.get_indices()
                if indices:
                    grouping.append((group.get_name(), indices))
            for i in range(self.ungrouped_list.count()):
                item = self.ungrouped_list.item(i)
                idx = item.data(USER_ROLE)
                grouping.append((item.text(), [idx]))

            ignored_indices = []
            for i in range(self.ignored_list.count()):
                item = self.ignored_list.item(i)
                ignored_indices.append(item.data(USER_ROLE))

            return grouping, ignored_indices

    return LayerGroupDialog(layer_names, parent, show_groups=enable_grouping,
                            pre_groups=pre_groups)


def show_update_dialog(new_layer_names, active_names, ignored_names):
    """
    Affiche le dialog d'update avec 5 colonnes :
      - Active (read-only, vert)
      - Discarded (read-only, rouge)
      - New Layers (draggable, teal)
      - Groups (drag-drop)
      - Ignore (drag-drop, rouge)

    Retourne (grouping, ignored_indices) pour les NEW layers uniquement,
    ou None si annule.
    """
    QtWidgets, _ = _import_qt()

    parent = QtWidgets.QApplication.activeWindow()
    dialog = _build_update_dialog(new_layer_names, active_names, ignored_names, parent)

    if _USE_PYSIDE6:
        accepted = dialog.exec()
    else:
        accepted = dialog.exec_()

    if accepted:
        return dialog.get_result()
    return None


def _build_update_dialog(new_layer_names, active_names, ignored_names, parent):
    """Construit le dialog d'update avec le bon PySide."""
    QtWidgets, QtCore = _import_qt()
    Qt = QtCore.Qt

    if _USE_PYSIDE6:
        USER_ROLE = Qt.ItemDataRole.UserRole
        ALIGN_TOP = Qt.AlignmentFlag.AlignTop
        MOVE_ACTION = Qt.DropAction.MoveAction
        DRAG_DROP = QtWidgets.QAbstractItemView.DragDropMode.DragDrop
        EXT_SELECT = QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        FRAME_BOX = QtWidgets.QFrame.Shape.Box
        FRAME_PLAIN = QtWidgets.QFrame.Shadow.Plain
        SIZE_EXPAND = QtWidgets.QSizePolicy.Policy.Expanding
        SIZE_MIN = QtWidgets.QSizePolicy.Policy.Minimum
        BTN_OK = QtWidgets.QDialogButtonBox.StandardButton.Ok
        BTN_CANCEL = QtWidgets.QDialogButtonBox.StandardButton.Cancel
        NO_DRAG = QtWidgets.QAbstractItemView.DragDropMode.NoDragDrop
        NO_SELECT = QtWidgets.QAbstractItemView.SelectionMode.NoSelection
    else:
        USER_ROLE = Qt.UserRole
        ALIGN_TOP = Qt.AlignTop
        MOVE_ACTION = Qt.MoveAction
        DRAG_DROP = QtWidgets.QAbstractItemView.DragDrop
        EXT_SELECT = QtWidgets.QAbstractItemView.ExtendedSelection
        FRAME_BOX = QtWidgets.QFrame.Box
        FRAME_PLAIN = QtWidgets.QFrame.Plain
        SIZE_EXPAND = QtWidgets.QSizePolicy.Expanding
        SIZE_MIN = QtWidgets.QSizePolicy.Minimum
        BTN_OK = QtWidgets.QDialogButtonBox.Ok
        BTN_CANCEL = QtWidgets.QDialogButtonBox.Cancel
        NO_DRAG = QtWidgets.QAbstractItemView.NoDragDrop
        NO_SELECT = QtWidgets.QAbstractItemView.NoSelection

    # ------------------------------------------------------------------
    #  DropListWidget (reutilisable)
    # ------------------------------------------------------------------
    class DropListWidget(QtWidgets.QListWidget):

        def __init__(self, par=None):
            super().__init__(par)
            self.setAcceptDrops(True)
            self.setDragEnabled(True)
            self.setDragDropMode(DRAG_DROP)
            self.setDefaultDropAction(MOVE_ACTION)
            self.setSelectionMode(EXT_SELECT)

        def dragEnterEvent(self, event):
            if event.source() and isinstance(event.source(), QtWidgets.QListWidget):
                event.acceptProposedAction()
            else:
                event.ignore()

        def dragMoveEvent(self, event):
            if event.source() and isinstance(event.source(), QtWidgets.QListWidget):
                event.acceptProposedAction()
            else:
                event.ignore()

        def dropEvent(self, event):
            source = event.source()
            if not source or not isinstance(source, QtWidgets.QListWidget) or source is self:
                event.ignore()
                return
            items_data = []
            for item in source.selectedItems():
                items_data.append((item.text(), item.data(USER_ROLE)))
            for item in reversed(source.selectedItems()):
                source.takeItem(source.row(item))
            for text, idx in items_data:
                new_item = QtWidgets.QListWidgetItem(text)
                new_item.setData(USER_ROLE, idx)
                self.addItem(new_item)
            event.acceptProposedAction()

    # ------------------------------------------------------------------
    #  GroupWidget (reutilisable)
    # ------------------------------------------------------------------
    class GroupWidget(QtWidgets.QFrame):

        def __init__(self, name, parent_dialog):
            super().__init__()
            self.parent_dialog = parent_dialog
            self.setFrameStyle(FRAME_BOX | FRAME_PLAIN)
            self.setLineWidth(1)

            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(4, 4, 4, 4)
            layout.setSpacing(4)

            header = QtWidgets.QHBoxLayout()
            self.name_edit = QtWidgets.QLineEdit(name)
            self.name_edit.setStyleSheet("font-weight: bold;")
            header.addWidget(self.name_edit)

            delete_btn = QtWidgets.QPushButton("X")
            delete_btn.setFixedWidth(24)
            delete_btn.clicked.connect(self._on_delete)
            header.addWidget(delete_btn)
            layout.addLayout(header)

            self.layer_list = DropListWidget()
            self.layer_list.setMinimumHeight(40)
            self.layer_list.setSizePolicy(SIZE_EXPAND, SIZE_MIN)
            layout.addWidget(self.layer_list)

        def _on_delete(self):
            self.parent_dialog._return_items_from_group(self)
            self.parent_dialog._remove_group_widget(self)

        def get_indices(self):
            indices = []
            for i in range(self.layer_list.count()):
                item = self.layer_list.item(i)
                indices.append(item.data(USER_ROLE))
            return indices

        def get_name(self):
            return self.name_edit.text().strip() or "Group"

    # ------------------------------------------------------------------
    #  UpdateLayerDialog
    # ------------------------------------------------------------------
    class UpdateLayerDialog(QtWidgets.QDialog):

        def __init__(self, new_names, active, ignored, par=None):
            super().__init__(par)
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.setWindowTitle("Update PSD — Layer Selection")
            self.setMinimumSize(900, 450)
            self.resize(1000, 550)

            self._group_counter = 0
            self._group_widgets = []

            main_layout = QtWidgets.QVBoxLayout(self)
            columns = QtWidgets.QHBoxLayout()

            # -- Col 1 : Active (read-only, vert) ---------------------------------
            col_active = QtWidgets.QVBoxLayout()
            lbl_active = QtWidgets.QLabel("Active Layers")
            lbl_active.setStyleSheet("font-weight: bold; color: #88cc88;")
            col_active.addWidget(lbl_active)
            self.active_list = QtWidgets.QListWidget()
            self.active_list.setDragDropMode(NO_DRAG)
            self.active_list.setSelectionMode(NO_SELECT)
            self.active_list.setStyleSheet(
                "QListWidget { border: 2px solid #446644; background: #111a11; }"
                "QListWidget::item { color: #88cc88; }")
            for name in active:
                self.active_list.addItem(name)
            col_active.addWidget(self.active_list)
            columns.addLayout(col_active, stretch=1)

            # -- Col 2 : Discarded (read-only, rouge) -----------------------------
            col_disc = QtWidgets.QVBoxLayout()
            lbl_disc = QtWidgets.QLabel("Discarded Layers")
            lbl_disc.setStyleSheet("font-weight: bold; color: #cc8888;")
            col_disc.addWidget(lbl_disc)
            self.discarded_list = QtWidgets.QListWidget()
            self.discarded_list.setDragDropMode(NO_DRAG)
            self.discarded_list.setSelectionMode(NO_SELECT)
            self.discarded_list.setStyleSheet(
                "QListWidget { border: 2px solid #664444; background: #1a1111; }"
                "QListWidget::item { color: #cc8888; }")
            for name in ignored:
                self.discarded_list.addItem(name)
            col_disc.addWidget(self.discarded_list)
            columns.addLayout(col_disc, stretch=1)

            # -- Col 3 : New Layers (draggable, teal) ------------------------------
            col_new = QtWidgets.QVBoxLayout()
            lbl_new = QtWidgets.QLabel("New Layers")
            lbl_new.setStyleSheet("font-weight: bold; color: #80dddd;")
            col_new.addWidget(lbl_new)
            self.new_list = DropListWidget()
            self.new_list.setStyleSheet(
                "QListWidget { border: 2px solid #447777; background: #111a1a; }"
                "QListWidget::item { color: #80dddd; }")
            for i, name in enumerate(new_names):
                item = QtWidgets.QListWidgetItem(name)
                item.setData(USER_ROLE, i)
                self.new_list.addItem(item)
            col_new.addWidget(self.new_list)

            ungroup_btn = QtWidgets.QPushButton("<< Ungroup")
            ungroup_btn.clicked.connect(self._ungroup_selected)
            col_new.addWidget(ungroup_btn)
            columns.addLayout(col_new, stretch=1)

            # -- Col 4 : Groups (drag-drop) ----------------------------------------
            col_groups = QtWidgets.QVBoxLayout()
            col_groups.addWidget(QtWidgets.QLabel("Groups"))

            self.scroll_area = QtWidgets.QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_container = QtWidgets.QWidget()
            self.groups_layout = QtWidgets.QVBoxLayout(self.scroll_container)
            self.groups_layout.setAlignment(ALIGN_TOP)
            self.scroll_area.setWidget(self.scroll_container)
            col_groups.addWidget(self.scroll_area)

            add_group_btn = QtWidgets.QPushButton("+ Group")
            add_group_btn.clicked.connect(self._add_group)
            col_groups.addWidget(add_group_btn)
            columns.addLayout(col_groups, stretch=1)

            # -- Col 5 : Ignore (drag-drop, rouge) --------------------------------
            col_ignore = QtWidgets.QVBoxLayout()
            lbl_ignore = QtWidgets.QLabel("Ignore")
            lbl_ignore.setStyleSheet("font-weight: bold; color: #cc8888;")
            col_ignore.addWidget(lbl_ignore)
            self.ignored_list = DropListWidget()
            self.ignored_list.setStyleSheet(
                "QListWidget { border: 2px solid #664444; background: #1a1111; }")
            col_ignore.addWidget(self.ignored_list)
            columns.addLayout(col_ignore, stretch=1)

            main_layout.addLayout(columns)

            button_box = QtWidgets.QDialogButtonBox(BTN_OK | BTN_CANCEL)
            button_box.accepted.connect(self.accept)
            button_box.rejected.connect(self.reject)
            main_layout.addWidget(button_box)

        def _add_group(self):
            self._group_counter += 1
            group = GroupWidget("Group {}".format(self._group_counter), self)
            self._group_widgets.append(group)
            self.groups_layout.addWidget(group)

        def _remove_group_widget(self, group_widget):
            self._group_widgets.remove(group_widget)
            self.groups_layout.removeWidget(group_widget)
            group_widget.deleteLater()

        def _return_items_from_group(self, group_widget):
            lst = group_widget.layer_list
            while lst.count():
                item = lst.takeItem(0)
                new_item = QtWidgets.QListWidgetItem(item.text())
                new_item.setData(USER_ROLE, item.data(USER_ROLE))
                self.new_list.addItem(new_item)

        def _ungroup_selected(self):
            for group in self._group_widgets:
                selected = list(group.layer_list.selectedItems())
                for item in reversed(selected):
                    idx = item.data(USER_ROLE)
                    text = item.text()
                    group.layer_list.takeItem(group.layer_list.row(item))
                    new_item = QtWidgets.QListWidgetItem(text)
                    new_item.setData(USER_ROLE, idx)
                    self.new_list.addItem(new_item)

            selected = list(self.ignored_list.selectedItems())
            for item in reversed(selected):
                idx = item.data(USER_ROLE)
                text = item.text()
                self.ignored_list.takeItem(self.ignored_list.row(item))
                new_item = QtWidgets.QListWidgetItem(text)
                new_item.setData(USER_ROLE, idx)
                self.new_list.addItem(new_item)

        def get_result(self):
            grouping = []
            for group in self._group_widgets:
                indices = group.get_indices()
                if indices:
                    grouping.append((group.get_name(), indices))
            for i in range(self.new_list.count()):
                item = self.new_list.item(i)
                idx = item.data(USER_ROLE)
                grouping.append((item.text(), [idx]))

            ignored_indices = []
            for i in range(self.ignored_list.count()):
                item = self.ignored_list.item(i)
                ignored_indices.append(item.data(USER_ROLE))

            return grouping, ignored_indices

    return UpdateLayerDialog(new_layer_names, active_names, ignored_names, parent)
