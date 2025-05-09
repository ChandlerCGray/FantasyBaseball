import sys
import os
import re
import pandas as pd
import glob

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QSplitter, QListWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QCheckBox, QTabWidget, QFileDialog, QMessageBox, QLabel,
    QFrame, QStatusBar, QDialog
)
from PySide6.QtCore import Qt

class DraftApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Draft Kit")
        self.resize(1400, 900)

        # ---------- Data references ----------
        self.master_df = pd.DataFrame()
        # Each tab: { "table": QTableWidget, "filter_func": callable,
        #             "sort_col": (str or None), "ascending": bool }
        self.tabs_info = {}
        self.drafted_order = []
        self.undo_stack = []

        # ---------- Improved Dark Mode Color & Style Setup ----------
        self.header_color = "#1B2631"         # Dark slate for headers
        self.header_text_color = "#DCE1E3"      # Muted off-white for header text
        self.accent_color = "#2A8C84"           # Muted teal for accents
        self.accent_hover_color = "#23756B"     # Darker muted teal for hover state
        self.background_color = "#121212"       # Deep dark background
        self.panel_color = "#121212"            # Panel background remains deep dark
        self.even_row_color = "#1A1A1A"         # Subtly lighter dark for even rows
        self.odd_row_color  = "#121212"         # Odd rows same as background for consistency
        self.selection_color = "#23756B"        # Using the hover tone for selections
        self.vertical_header_bg = "#2C3E50"     # Dark blue-grey for vertical headers
        self.vertical_header_fg = "#DCE1E3"     # Muted off-white for vertical header text

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background-color: {self.header_color};")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)

        title_label = QLabel("Draft Kit")
        title_label.setStyleSheet(f"color: {self.header_text_color}; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)

        main_layout.addWidget(header_frame)

        # QSplitter for left panel (Draft Log) and right panel (controls + tabs)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Left panel: Draft log
        left_panel = QWidget()
        left_panel.setStyleSheet(f"background-color: {self.panel_color};")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(5)

        log_label = QLabel("Draft Log")
        log_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_layout.addWidget(log_label)

        self.draft_log = QListWidget()
        # Updated background to match left panel
        self.draft_log.setStyleSheet(f"background-color: {self.panel_color};")
        left_layout.addWidget(self.draft_log, 1)

        clear_log_button = QPushButton("Clear Log")
        clear_log_button.setStyleSheet(self.button_style())
        clear_log_button.clicked.connect(self.clear_draft_log)
        left_layout.addWidget(clear_log_button)

        splitter.addWidget(left_panel)

        # Right panel: top controls + QTabWidget
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(5)

        # Top controls
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(5)

        search_label = QLabel("Search:")
        controls_layout.addWidget(search_label)

        self.search_entry = QLineEdit()
        # Press Enter => search
        self.search_entry.returnPressed.connect(self.search_all_tabs)
        self.search_entry.textChanged.connect(self.search_all_tabs)
        controls_layout.addWidget(self.search_entry)

        self.search_button = QPushButton("Search")
        self.search_button.setStyleSheet(self.button_style())
        self.search_button.clicked.connect(self.search_all_tabs)
        controls_layout.addWidget(self.search_button)

        self.clear_search_button = QPushButton("Clear Search")
        self.clear_search_button.setStyleSheet(self.button_style())
        self.clear_search_button.clicked.connect(self.clear_search)
        controls_layout.addWidget(self.clear_search_button)

        self.compare_button = QPushButton("Compare Selected")
        self.compare_button.setStyleSheet(self.button_style())
        self.compare_button.clicked.connect(self.compare_selected)
        controls_layout.addWidget(self.compare_button)

        self.hide_drafted_cb = QCheckBox("Hide Drafted")
        self.hide_drafted_cb.stateChanged.connect(self.refresh_all_tabs)
        controls_layout.addWidget(self.hide_drafted_cb)

        controls_layout.addStretch(1)

        self.open_button = QPushButton("Open Workbook")
        self.open_button.setStyleSheet(self.button_style())
        self.open_button.clicked.connect(self.open_workbook)
        controls_layout.addWidget(self.open_button)

        right_layout.addWidget(controls_widget, 0)

        # Tabs
        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs, 1)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 1100])

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def button_style(self):
        return (
            f"QPushButton {{"
            f"  background-color: {self.accent_color};"
            f"  color: #FFFFFF;"
            f"  border-radius: 3px;"
            f"  padding: 5px 10px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {self.accent_hover_color};"
            f"}}"
        )

    # -------------- Workbook / Tabs --------------
    def open_workbook(self):
        # Compute the directory paths: src directory, project root, and then output folder
        src_dir = os.path.abspath(os.path.dirname(__file__))
        project_root = os.path.abspath(os.path.join(src_dir, ".."))
        output_folder = os.path.join(project_root, "output")
        
        # Find all .xlsx files in the output folder
        xlsx_files = glob.glob(os.path.join(output_folder, "*.xlsx"))
        newest_file = ""
        if xlsx_files:
            newest_file = max(xlsx_files, key=os.path.getmtime)
        
        # Initialize the file dialog with the output folder as the starting directory
        file_dialog = QFileDialog(self, "Open Excel Workbook", output_folder, "Excel Files (*.xlsx *.xls);;All Files (*)")
        if newest_file:
            file_dialog.selectFile(newest_file)
        
        if file_dialog.exec() == QFileDialog.Accepted:
            filepath = file_dialog.selectedFiles()[0]
        else:
            return
        
        if not filepath:
            return
        
        try:
            excel_file = pd.ExcelFile(filepath)
            sheets = {sheet: excel_file.parse(sheet) for sheet in excel_file.sheet_names}
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load workbook:\n{e}")
            return
        
        if "All players" not in sheets:
            QMessageBox.critical(self, "Error", "Workbook must contain an 'All players' sheet.")
            return
        
        self.master_df = sheets["All players"].copy()
        self.master_df["Drafted"] = False
        
        # Clear existing tabs, log, etc.
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)
        self.tabs_info.clear()
        self.draft_log.clear()
        self.drafted_order.clear()
        self.undo_stack.clear()
        
        # "All players" tab
        self.create_tab("All players", lambda df: df)
        
        # Additional tabs
        for sheet_name in excel_file.sheet_names:
            if sheet_name == "All players":
                continue
            if sheet_name.lower() == "c":
                filter_func = lambda df: df[df["Eligible_Positions"].astype(str).str.contains(r'\bC\b', flags=re.IGNORECASE, na=False)]
            elif sheet_name.lower() == "overall hitters":
                filter_func = lambda df: df[~df["Eligible_Positions"].astype(str).str.contains("P", case=False, na=False)]
            elif sheet_name.lower() == "overall pitchers":
                filter_func = lambda df: df[df["Eligible_Positions"].astype(str).str.contains("P", case=False, na=False)]
            else:
                def pos_filter(df, pos=sheet_name):
                    return df[df["Eligible_Positions"].astype(str).str.contains(pos, case=False, na=False)]
                filter_func = lambda df, f=pos_filter: f(df)
        
            self.create_tab(sheet_name, filter_func)
        
        self.status_bar.showMessage(f"Loaded {os.path.basename(filepath)} with {len(excel_file.sheet_names)} sheets.")

    def create_tab(self, tab_name, filter_func):
        table = QTableWidget()
        # Additional styling for a modern look
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
            f"QTableWidget::item:selected {{"
            f"  background-color: {self.selection_color};"
            f"  color: #FFFFFF;"
            f"}}"
            f"QHeaderView::section {{"
            f"  background-color: #34495E;"
            f"  color: #FFFFFF;"
            f"  font-weight: bold;"
            f"  border: none;"
            f"}}"
        )
        # Show row numbers with padding
        table.verticalHeader().setVisible(True)
        table.verticalHeader().setDefaultSectionSize(24)
        table.verticalHeader().setStyleSheet(
            f"QHeaderView::section {{ background-color: {self.vertical_header_bg}; color: {self.vertical_header_fg}; padding: 0 10px; }}"
        )
        table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)

        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.ExtendedSelection)

        # Enable column sorting
        table.setSortingEnabled(True)
        # Connect to store the sorted column name / ascending state
        header = table.horizontalHeader()
        header.sortIndicatorChanged.connect(lambda col, order, tn=tab_name: self.store_sort_info(tn, col, order))

        # Double-click => toggle drafted
        table.cellDoubleClicked.connect(lambda row, col, tn=tab_name: self.toggle_drafted(table, row, col, tn))

        # Add the tab
        idx = self.tabs.addTab(table, tab_name)
        self.tabs_info[tab_name] = {
            "table": table,
            "filter_func": filter_func,
            "sort_col": None,    # DataFrame column name
            "ascending": True
        }
        self.refresh_tab(tab_name)

    def store_sort_info(self, tab_name, col_index, sort_order):
        """
        Called whenever the user clicks a column header to sort.
        We map the QTableWidget column index to the DataFrame column name,
        store whether it's ascending or descending, and re-refresh the tab.
        """
        if tab_name not in self.tabs_info:
            return
        info = self.tabs_info[tab_name]
        table = info["table"]
        if table.columnCount() == 0:
            return

        # Map col_index to the actual column name
        if col_index < 0 or col_index >= table.columnCount():
            return
        df_columns = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
        if col_index >= len(df_columns):
            return

        col_name = df_columns[col_index]
        ascending = (sort_order == Qt.AscendingOrder)
        info["sort_col"] = col_name
        info["ascending"] = ascending

        # Re-refresh to apply numeric sorting in the DataFrame
        self.refresh_tab(tab_name)

    def refresh_tab(self, tab_name):
        info = self.tabs_info[tab_name]
        table = info["table"]
        filter_func = info["filter_func"]
        sort_col = info["sort_col"]
        ascending = info["ascending"]

        df = filter_func(self.master_df.copy())
        if self.hide_drafted_cb.isChecked():
            df = df[df["Drafted"] == False]

        # Re-apply the user's last chosen sort if we have a valid column name
        if sort_col and sort_col in df.columns:
            # Sort the DataFrame numerically or lexicographically
            # Pandas will guess numeric if the column is numeric
            df = df.sort_values(by=sort_col, ascending=ascending)

        self.fill_table(table, df)

    def fill_table(self, table, df):
        # Disable built-in sorting to avoid conflicts
        table.setSortingEnabled(False)
        table.clear()
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns.tolist())

        for row_index, row_data in enumerate(df.itertuples(index=False)):
            for col_index, value in enumerate(row_data):
                item = self.create_item_for_value(value)
                table.setItem(row_index, col_index, item)

        table.resizeColumnsToContents()
        # Re-enable sorting after populating the table
        table.setSortingEnabled(True)

    def create_item_for_value(self, value):
        """
        Parse the value to float if possible.
        If numeric, store as numeric data with up to 3 decimals.
        Otherwise, store as a string.
        """
        try:
            float_val = float(value)
            item = QTableWidgetItem()
            # Store numeric data so sorting is correct
            item.setData(Qt.EditRole, float_val)
            # Display with 3 decimal places
            item.setText(f"{float_val:.3f}")
            return item
        except ValueError:
            # Not numeric, treat as string
            return QTableWidgetItem(str(value))

    def refresh_all_tabs(self):
        for tn in self.tabs_info.keys():
            self.refresh_tab(tn)

    # -------------- Searching --------------
    def search_all_tabs(self):
        query = self.search_entry.text().strip().lower()
        if not query:
            self.refresh_all_tabs()
            self.status_bar.showMessage("Search cleared.")
            return

        for tn, info in self.tabs_info.items():
            table = info["table"]
            filter_func = info["filter_func"]
            sort_col = info["sort_col"]
            ascending = info["ascending"]

            df = filter_func(self.master_df.copy())
            if self.hide_drafted_cb.isChecked():
                df = df[df["Drafted"] == False]

            df = df[df.apply(lambda row: query in " ".join(str(x).lower() for x in row.values), axis=1)]

            # Re-apply the user's last chosen sort if available
            if sort_col and sort_col in df.columns:
                df = df.sort_values(by=sort_col, ascending=ascending)

            table.clear()
            table.setRowCount(len(df))
            table.setColumnCount(len(df.columns))
            table.setHorizontalHeaderLabels(df.columns.tolist())

            for row_index, row_data in enumerate(df.itertuples(index=False)):
                for col_index, value in enumerate(row_data):
                    item = self.create_item_for_value(value)
                    table.setItem(row_index, col_index, item)

            table.resizeColumnsToContents()

        self.status_bar.showMessage(f"Search '{query}' applied to all tabs.")

    def clear_search(self):
        self.search_entry.clear()
        self.refresh_all_tabs()
        self.status_bar.showMessage("Search cleared.")

    # -------------- Draft Toggles & Log --------------
    def toggle_drafted(self, table, row, col, tab_name):
        columns = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
        if "Name" not in columns:
            QMessageBox.critical(self, "Error", "No 'Name' column found.")
            return
        name_col_index = columns.index("Name")

        name_item = table.item(row, name_col_index)
        if not name_item:
            return
        player_name = name_item.text()

        mask = self.master_df["Name"] == player_name
        if mask.sum() == 0:
            QMessageBox.information(self, "Info", f"Player '{player_name}' not found in master data.")
            return
        current_value = bool(self.master_df.loc[mask, "Drafted"].iloc[0])
        new_value = not current_value
        self.master_df.loc[mask, "Drafted"] = new_value

        self.undo_stack.append((player_name, current_value))

        if new_value:
            if player_name not in self.drafted_order:
                self.drafted_order.append(player_name)
        else:
            if player_name in self.drafted_order:
                self.drafted_order.remove(player_name)

        self.update_draft_log()
        self.status_bar.showMessage(f"Player '{player_name}' marked as {'Drafted' if new_value else 'Available'}.")
        # Refresh all tabs so the new data/filters are consistent
        self.refresh_all_tabs()

    def update_draft_log(self):
        self.draft_log.clear()
        for i, player in enumerate(self.drafted_order, start=1):
            self.draft_log.addItem(f"Pick {i}: {player}")

    def clear_draft_log(self):
        self.drafted_order.clear()
        self.draft_log.clear()
        self.status_bar.showMessage("Draft log cleared.")

    def undo_last_action(self):
        if not self.undo_stack:
            QMessageBox.information(self, "Undo", "No actions to undo.")
            return
        player_name, previous_state = self.undo_stack.pop()
        mask = self.master_df["Name"] == player_name
        self.master_df.loc[mask, "Drafted"] = previous_state
        if previous_state:
            if player_name not in self.drafted_order:
                self.drafted_order.append(player_name)
        else:
            if player_name in self.drafted_order:
                self.drafted_order.remove(player_name)
        self.update_draft_log()
        self.status_bar.showMessage(f"Undo: Player '{player_name}' reverted to {'Drafted' if previous_state else 'Available'}.")
        self.refresh_all_tabs()

    # -------------- Compare Players --------------
    def compare_selected(self):
        current_index = self.tabs.currentIndex()
        if current_index < 0:
            QMessageBox.information(self, "Compare", "No active tab selected.")
            return
        tab_name = self.tabs.tabText(current_index)
        info = self.tabs_info.get(tab_name)
        if not info:
            QMessageBox.information(self, "Compare", "No data in this tab.")
            return
        table = info["table"]
        selected_ranges = table.selectedRanges()
        if not selected_ranges:
            QMessageBox.information(self, "Compare", "Please select at least one player to compare.")
            return

        selected_rows = set()
        for rng in selected_ranges:
            for row in range(rng.topRow(), rng.bottomRow() + 1):
                selected_rows.add(row)

        if not selected_rows:
            QMessageBox.information(self, "Compare", "Please select at least one player to compare.")
            return

        columns = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
        if "Name" not in columns:
            QMessageBox.critical(self, "Error", "No 'Name' column found.")
            return
        name_col_index = columns.index("Name")

        selected_names = []
        for row in selected_rows:
            name_item = table.item(row, name_col_index)
            if name_item:
                selected_names.append(name_item.text())

        if not selected_names:
            QMessageBox.information(self, "Compare", "No valid names selected.")
            return

        df = self.master_df[self.master_df["Name"].isin(selected_names)]
        if df.empty:
            QMessageBox.information(self, "Compare", "No matching data found for selected players.")
            return

        compare_dialog = QDialog(self)
        compare_dialog.setWindowTitle("Player Comparison")
        compare_dialog.resize(1000, 600)
        layout = QVBoxLayout(compare_dialog)

        compare_table = QTableWidget()
        compare_table.setRowCount(len(df))
        compare_table.setColumnCount(len(df.columns))
        compare_table.setHorizontalHeaderLabels(df.columns.tolist())
        compare_table.setAlternatingRowColors(True)
        compare_table.setStyleSheet(
            "QTableWidget::item:selected {"
            f"  background-color: {self.selection_color};"
            "  color: #FFFFFF;"
            "}"
            "QHeaderView::section {"
            "  background-color: #34495E;"
            "  color: #FFFFFF;"
            "  font-weight: bold;"
            "  border: none;"
            "}"
        )

        for r_index, row_data in enumerate(df.itertuples(index=False)):
            for c_index, value in enumerate(row_data):
                item = self.create_item_for_value(value)
                compare_table.setItem(r_index, c_index, item)

        compare_table.resizeColumnsToContents()
        layout.addWidget(compare_table)
        compare_dialog.exec()

    def fill_table(self, table, df):
        # Disable built-in sorting to avoid conflicts
        table.setSortingEnabled(False)
        table.clear()
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns.tolist())

        # Determine if there's a 'Tier' column and get its index
        tier_column_index = None
        for i, col in enumerate(df.columns):
            if col.lower() == "tier":
                tier_column_index = i
                break

        for row_index, row_data in enumerate(df.itertuples(index=False)):
            for col_index, value in enumerate(row_data):
                item = self.create_item_for_value(value)
                # If this is the Tier column, apply the gradient and adjust text color
                if tier_column_index is not None and col_index == tier_column_index:
                    try:
                        tier_val = int(value)
                        # Calculate interpolation factor between 0 (Tier 1) and 1 (Tier 5)
                        f = (tier_val - 1) / 4.0
                        red = int(f * 255)
                        green = int((1 - f) * 255)
                        blue = 0  # Fixed blue component for the gradient
                        bg_color = QtGui.QColor(red, green, blue)
                        item.setBackground(QtGui.QBrush(bg_color))
                        item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
                        
                    except Exception as e:
                        # If conversion fails, simply use default text colors
                        pass
                table.setItem(row_index, col_index, item)

        table.resizeColumnsToContents()
        # Re-enable sorting after populating the table
        table.setSortingEnabled(True)

    # -------------- Stubbed Analytics --------------
    def show_draft_vs_points(self):
        QMessageBox.information(self, "Analytics", "Draft Order vs. Projected Points not implemented yet.")

    def show_positional_scarcity(self):
        QMessageBox.information(self, "Analytics", "Positional Scarcity not implemented yet.")

def main():
    app = QApplication(sys.argv)
    window = DraftApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
