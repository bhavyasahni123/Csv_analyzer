
import sys
import io
from contextlib import redirect_stdout
from html import escape
from theme import set_dark_mode
from visualization import VisualizationWidget

import pandas as pd

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTabWidget,
    QHeaderView,
    QSizePolicy,
    QAbstractItemView,
)


from main import (
    load_dataset,
    show_overview,
    show_missing_values,
    show_numerical_statistics,
    show_categorical_statistics,
    show_category_frequencies,
    show_column_details,
)


class DataAnalysisDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.df = None
        self.is_dark = True

        self.setWindowTitle("Datara — CSV Analyzer")
        self.resize(1200, 750)
        self.setMinimumSize(800, 550)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        set_dark_mode(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(24, 18, 24, 14)
        self.layout.setSpacing(12)

        self.create_header()
        self.create_buttons()
        self.create_content()
        self.on_theme_changed(True)
        self.create_status_bar()

        self.show_empty_table()

    def create_header(self):
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        self.heading = QLabel("Datara — CSV Analyzer")
        self.heading.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
        """)

        top_bar.addWidget(self.heading)
        top_bar.addStretch()

        self.layout.addLayout(top_bar)

    def create_buttons(self):
        button_bar = QHBoxLayout()
        button_bar.setSpacing(12)

        self.load_button = QPushButton("Load CSV")
        self.preview_button = QPushButton("Preview Data")
        self.report_button = QPushButton("Generate Report")

        for button in (
            self.load_button,
            self.preview_button,
            self.report_button,
        ):
            button.setMinimumHeight(38)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            button_bar.addWidget(button)

        self.load_button.clicked.connect(self.load_csv)
        self.preview_button.clicked.connect(self.preview_data)
        self.report_button.clicked.connect(self.generate_report)

        self.layout.addLayout(button_bar)

    def create_content(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        preview_page = QWidget()
        preview_layout = QVBoxLayout(preview_page)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        preview_layout.setSpacing(8)

        self.preview_label = QLabel("Dataset Preview")
        self.preview_label.setStyleSheet("""
            font-size: 17px;
            font-weight: 600;
            padding-top: 4px;
        """)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.setSortingEnabled(False)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.table, 1)
        self.tabs.addTab(preview_page, "Preview")

    
        report_page = QWidget()
        report_layout = QVBoxLayout(report_page)
        report_layout.setContentsMargins(8, 8, 8, 8)

        self.report_output = QTextEdit()
        self.report_output.setReadOnly(True)
        self.report_output.setAcceptRichText(True)
        self.report_output.setLineWrapMode(
            QTextEdit.LineWrapMode.WidgetWidth
        )
        self.report_output.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        report_layout.addWidget(self.report_output)
        self.tabs.addTab(report_page, "Report")

        self.visualization_widget = VisualizationWidget()
        self.tabs.addTab(self.visualization_widget, "Visualizations")

        self.layout.addWidget(self.tabs, 1)

    def on_theme_changed(self, is_dark=True):
        """Keep the chart workspace synchronized with the permanent dark theme."""
        self.is_dark = True
        self.visualization_widget.set_dark_mode(True)

        if self.df is not None and self.tabs.currentIndex() == 1:
            self.report_output.setHtml(self.build_report_html())

    def create_status_bar(self):
        self.status_label = QLabel(
            "No dataset loaded. Click 'Load CSV' to begin."
        )
        self.status_label.setMinimumHeight(22)
        self.layout.addWidget(self.status_label)

    def show_empty_table(self, message=None):
        if message is None:
            message = (
                "No data loaded\n\n"
                "Click 'Load CSV' to select a CSV or TSV file."
            )

        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Dataset Preview"])
        self.table.verticalHeader().setVisible(False)

        item = QTableWidgetItem(message)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(0, 0, item)

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.preview_label.show()
        self.tabs.setCurrentIndex(0)
        self.table.show()

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Dataset",
            "",
            "Data Files (*.csv *.tsv *.txt);;All Files (*)",
        )

        if not file_path:
            return

        try:
            if file_path.lower().endswith(".tsv"):
                df = pd.read_csv(file_path, sep="\t")
            elif file_path.lower().endswith(".txt"):
                df = pd.read_csv(
                    file_path,
                    sep=None,
                    engine="python",
                )
            else:
                df = load_dataset(file_path)

            if df is None:
                raise ValueError("The dataset could not be loaded.")

            self.df = df
            self.visualization_widget.set_dataframe(self.df)

            self.show_empty_table(
                "Dataset loaded successfully\n\n"
                f"Rows: {len(self.df):,}\n"
                f"Columns: {len(self.df.columns):,}\n\n"
                "Click 'Preview Data' to display the first 100 rows."
            )

            self.status_label.setText(
                f"Loaded {len(self.df):,} rows and "
                f"{len(self.df.columns):,} columns"
            )

        except Exception as error:
            self.df = None
            self.show_empty_table(
                "Unable to load the selected file.\n\n"
                f"{error}"
            )
            self.status_label.setText("Dataset loading failed.")

    def preview_data(self):
        if self.df is None:
            self.status_label.setText(
                "Please load a CSV or TSV file first."
            )
            return

        try:
            preview_df = self.df.head(100)

            self.table.setSortingEnabled(False)
            self.table.clear()
            self.table.setRowCount(len(preview_df))
            self.table.setColumnCount(len(preview_df.columns))
            self.table.setHorizontalHeaderLabels(
                [str(column) for column in preview_df.columns]
            )
            self.table.verticalHeader().setVisible(True)

            for row_index, row in enumerate(
                preview_df.itertuples(index=False, name=None)
            ):
                for column_index, value in enumerate(row):
                    if pd.isna(value):
                        display_value = ""
                    else:
                        display_value = str(value)

                    self.table.setItem(
                        row_index,
                        column_index,
                        QTableWidgetItem(display_value),
                    )

            self.table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            self.table.resizeColumnsToContents()

            for column in range(self.table.columnCount()):
                self.table.setColumnWidth(
                    column,
                    min(self.table.columnWidth(column), 300),
                )

            self.table.verticalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )

            self.tabs.setCurrentIndex(0)
            self.preview_label.show()
            self.table.show()

            self.status_label.setText(
                f"Showing {len(preview_df):,} of "
                f"{len(self.df):,} rows and "
                f"{len(self.df.columns):,} columns"
            )

        except Exception as error:
            self.status_label.setText(f"Preview failed: {error}")

    def build_report_html(self):
        df = self.df

        total_rows = len(df)
        total_columns = len(df.columns)
        total_cells = total_rows * total_columns
        missing_cells = int(df.isna().sum().sum())
        complete_cells = total_cells - missing_cells
        missing_percent = (
            (missing_cells / total_cells * 100)
            if total_cells else 0
        )
        memory_bytes = int(df.memory_usage(deep=True).sum())

        numerical_df = df.select_dtypes(include="number")
        categorical_df = df.select_dtypes(
            include=["object", "category", "bool", "string"]
        )

        missing_df = pd.DataFrame({
            "Column": df.columns.astype(str),
            "Data Type": df.dtypes.astype(str).values,
            "Missing Values": df.isna().sum().values,
            "Missing (%)": (
                df.isna().mean().values * 100
            ),
        })

        missing_df = missing_df.sort_values(
            "Missing Values",
            ascending=False,
        )

        numerical_stats = (
            numerical_df.describe().T.reset_index()
            if not numerical_df.empty
            else pd.DataFrame()
        )

        categorical_stats = (
            categorical_df.describe().T.reset_index()
            if not categorical_df.empty
            else pd.DataFrame()
        )

        def format_cell(value):
            if pd.isna(value):
                return "—"
            if isinstance(value, float):
                return f"{value:,.3f}"
            return str(value)

        def dataframe_to_html(dataframe, empty_message):
            if dataframe.empty:
                return (
                    '<p class="empty">'
                    + escape(empty_message)
                    + "</p>"
                )

            headers = "".join(
                f"<th>{escape(str(column))}</th>"
                for column in dataframe.columns
            )

            rows = []

            for row in dataframe.itertuples(index=False, name=None):
                cells = "".join(
                    f"<td>{escape(format_cell(value))}</td>"
                    for value in row
                )
                rows.append(f"<tr>{cells}</tr>")

            return (
                '<div class="table-wrap"><table><thead><tr>'
                + headers
                + "</tr></thead><tbody>"
                + "".join(rows)
                + "</tbody></table></div>"
            )

        def capture_analysis(title, function):
            buffer = io.StringIO()
            try:
                with redirect_stdout(buffer):
                    function(df)
                text = buffer.getvalue().strip()
                if not text:
                    return ""
                return (
                    f'<h3>{escape(title)}</h3>'
                    f'<pre>{escape(text)}</pre>'
                )
            except Exception as error:
                return (
                    f'<h3>{escape(title)}</h3>'
                    f'<p class="empty">Unable to generate this section: '
                    f'{escape(str(error))}</p>'
                )

        cards = [
            ("Rows", f"{total_rows:,}", "Records in dataset"),
            ("Columns", f"{total_columns:,}", "Variables available"),
            ("Missing Values", f"{missing_cells:,}", f"{missing_percent:.2f}% of all cells"),
            ("Memory Usage", f"{memory_bytes / 1024:.1f} KB", "Approximate DataFrame memory"),
        ]

        cards_html = "".join(
            f"""
            <div class="metric">
                <div class="metric-label">{escape(label)}</div>
                <div class="metric-value">{escape(value)}</div>
                <div class="metric-note">{escape(note)}</div>
            </div>
            """
            for label, value, note in cards
        )

        if self.is_dark:
            report_bg = "#171923"
            report_text = "#e8eaf0"
            report_muted = "#a5adbd"
            report_surface = "#222735"
            report_surface_alt = "#2b3142"
            report_border = "#3b4357"
        else:
            report_bg = "#FAF9F6"
            report_text = "#292929"
            report_muted = "#77736B"
            report_surface = "#F0EEE8"
            report_surface_alt = "#E5E3DD"
            report_border = "#D8D5CE"

        html = f"""
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: "Segoe UI", Arial, sans-serif;
                color: {report_text};
                background-color: {report_bg};
                margin: 16px;
                font-size: 13px;
            }}

            h1 {{
                font-size: 25px;
                margin: 0 0 6px 0;
            }}

            .subtitle {{
                color: {report_muted};
                margin-bottom: 20px;
            }}

            h2 {{
                font-size: 17px;
                margin-top: 25px;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 2px solid {report_border};
            }}

            h3 {{
                font-size: 14px;
                margin-top: 18px;
            }}

            .metrics {{
                margin-top: 12px;
            }}

            .metric {{
                background-color: {report_surface};
                border: 1px solid {report_border};
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 8px;
            }}

            .metric-label {{
                color: {report_muted};
                font-size: 12px;
            }}

            .metric-value {{
                font-size: 23px;
                font-weight: bold;
                margin-top: 5px;
                margin-bottom: 4px;
            }}

            .metric-note {{
                color: {report_muted};
                font-size: 11px;
            }}

            .table-wrap {{
                margin-top: 8px;
                margin-bottom: 16px;
            }}

            table {{
                border-collapse: collapse;
                width: 100%;
            }}

            th {{
                background-color: {report_surface_alt};
                font-weight: bold;
                text-align: left;
            }}

            th, td {{
                padding: 8px;
                border: 1px solid {report_border};
            }}

            tr:nth-child(even) {{
                background-color: {report_surface};
            }}

            pre {{
                white-space: pre-wrap;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
                background-color: {report_surface};
                border: 1px solid {report_border};
                border-radius: 6px;
                padding: 12px;
            }}

            .empty {{
                color: {report_muted};
                padding: 8px 0;
            }}

            .footer {{
                color: {report_muted};
                margin-top: 24px;
                padding-top: 12px;
                border-top: 1px solid {report_border};
            }}
        </style>
        </head>
        <body>
            <h1>Dataset Analysis Report</h1>
            <div class="subtitle">
                Overview, data quality and statistical summaries
            </div>

            <h2>Dataset Overview</h2>
            <div class="metrics">{cards_html}</div>

            <h2>Data Quality</h2>
            {dataframe_to_html(
                missing_df,
                "No columns available."
            )}

            <h2>Numerical Statistics</h2>
            {dataframe_to_html(
                numerical_stats,
                "No numerical columns found in this dataset."
            )}

            <h2>Categorical Statistics</h2>
            {dataframe_to_html(
                categorical_stats,
                "No categorical columns found in this dataset."
            )}

            <h2>Additional Analysis</h2>
            {capture_analysis("Category Frequencies", show_category_frequencies)}
            {capture_analysis("Column Details", show_column_details)}

            <div class="footer">
                Report generated from the currently loaded dataset.
                Complete cells: {complete_cells:,} of {total_cells:,}.
            </div>
        </body>
        </html>
        """

        return html

    def generate_report(self):
        if self.df is None:
            self.status_label.setText(
                "Please load a dataset before generating a report."
            )
            return

        try:
            html = self.build_report_html()
            self.report_output.setHtml(html)

            self.tabs.setCurrentIndex(1)
            self.report_output.show()

            self.status_label.setText(
                "Analysis report generated successfully."
            )

        except Exception as error:
            self.status_label.setText(
                f"Report generation failed: {error}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = DataAnalysisDashboard()
    window.show()

    sys.exit(app.exec())
