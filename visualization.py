from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView


class VisualizationWidget(QWidget):
    """Automatically create a multi-chart exploration dashboard for a DataFrame."""

    MAX_POINTS = 1800
    MAX_NUMERIC_CHARTS = 8
    MAX_CATEGORY_CHARTS = 6
    TOP_CATEGORIES = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self.df = pd.DataFrame()
        self.is_dark = False

        self.message_label = QLabel(
            "Load a CSV, TSV, or TXT file. Charts will be generated automatically; "
            "there are no chart-selection forms."
        )
        self.message_label.setWordWrap(True)
        self.chart_view = QWebEngineView()
        self.chart_view.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.addWidget(self.message_label)
        layout.addWidget(self.chart_view, 1)
        self._show_placeholder()

    def set_dataframe(self, dataframe: pd.DataFrame):
        self.df = dataframe.copy() if dataframe is not None else pd.DataFrame()
        if self.df.empty:
            self.message_label.setText("No dataset loaded. Load a CSV, TSV, or TXT file first.")
            self._show_placeholder()
            return
        self.message_label.setText(
            f"Automatic exploration · {len(self.df):,} rows × {len(self.df.columns):,} columns · "
            "Charts are selected from the detected data types."
        )
        self.generate_dashboard()

    def set_dark_mode(self, is_dark: bool):
        self.is_dark = bool(is_dark)
        if self.df.empty:
            self._show_placeholder()
        else:
            self.generate_dashboard()

    def _show_placeholder(self):
        bg = "#171923" if self.is_dark else "#FAF9F6"
        fg = "#E8EAF0" if self.is_dark else "#292929"
        html = f"""<!doctype html><html><head><meta charset='utf-8'></head>
        <body style='background:{bg};color:{fg};font-family:Arial,sans-serif;display:flex;
        align-items:center;justify-content:center;height:90vh;margin:0;text-align:center'>
        <div style='max-width:700px;padding:28px'><h2>Automatic Data Exploration</h2>
        <p>Load a dataset to automatically see numeric distributions, category counts and shares,
        trends, outliers, relationships, and missing-data patterns.</p></div></body></html>"""
        self.chart_view.setHtml(html, QUrl("https://localhost/"))

    @staticmethod
    def _safe_name(value) -> str:
        return str(value)

    def _sample(self, frame: pd.DataFrame) -> pd.DataFrame:
        if len(frame) <= self.MAX_POINTS:
            return frame
        positions = [round(i * (len(frame) - 1) / (self.MAX_POINTS - 1)) for i in range(self.MAX_POINTS)]
        return frame.iloc[positions]

    def generate_dashboard(self):
        if self.df.empty:
            self._show_placeholder()
            return

        df = self.df
        is_dark = self.is_dark
        template = "plotly_dark" if is_dark else "plotly_white"
        bg = "#171923" if is_dark else "#FAF9F6"
        fg = "#E8EAF0" if is_dark else "#292929"
        muted = "#A5ADBD" if is_dark else "#77736B"
        grid = "#3B4357" if is_dark else "#D8D5CE"

        numeric_cols = list(df.select_dtypes(include="number").columns)
        date_cols = []
        for col in df.columns:
            series = df[col]
            if pd.api.types.is_datetime64_any_dtype(series):
                date_cols.append(col)
            elif any(token in str(col).lower() for token in ("date", "time", "timestamp")):
                sample = series.dropna().head(300)
                if not sample.empty:
                    parsed = pd.to_datetime(sample, errors="coerce")
                    if parsed.notna().mean() >= 0.7:
                        date_cols.append(col)

        categorical_cols = []
        for col in df.columns:
            series = df[col]
            if (pd.api.types.is_object_dtype(series)
                    or isinstance(series.dtype, pd.CategoricalDtype)
                    or pd.api.types.is_bool_dtype(series)
                    or pd.api.types.is_string_dtype(series)):
                if series.nunique(dropna=True) > 0:
                    categorical_cols.append(col)
        for col in numeric_cols:
            if pd.api.types.is_integer_dtype(df[col]) and 2 <= df[col].nunique(dropna=True) <= 15:
                if col not in categorical_cols:
                    categorical_cols.append(col)

        sections = []
        first_plot = True

        def add_figure(fig, title, description=""):
            nonlocal first_plot
            fig.update_layout(
                template=template,
                title=dict(text=title, x=0.02, xanchor="left", font=dict(size=20)),
                paper_bgcolor=bg,
                plot_bgcolor=bg,
                font=dict(color=fg, family="Arial, sans-serif"),
                margin=dict(l=55, r=35, t=75, b=55),
                autosize=True,
            )
            fig.update_xaxes(showgrid=True, gridcolor=grid, zerolinecolor=grid)
            fig.update_yaxes(showgrid=True, gridcolor=grid, zerolinecolor=grid)
            html = fig.to_html(
                full_html=False,
                include_plotlyjs="cdn" if first_plot else False,
                config={"responsive": True, "displaylogo": False, "scrollZoom": True},
            )
            first_plot = False
            desc = f"<p class='description'>{description}</p>" if description else ""
            sections.append(f"<section>{desc}{html}</section>")

        rows, cols = df.shape
        missing_cells = int(df.isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())
        cards = [
            ("Rows", f"{rows:,}"),
            ("Columns", f"{cols:,}"),
            ("Missing cells", f"{missing_cells:,}"),
            ("Duplicate rows", f"{duplicate_rows:,}"),
            ("Numeric columns", f"{len(numeric_cols):,}"),
            ("Categorical columns", f"{len(categorical_cols):,}"),
        ]
        cards_html = "".join(
            f"<div class='card'><div class='card-label'>{label}</div><div class='card-value'>{value}</div></div>"
            for label, value in cards
        )

        for col in numeric_cols[:self.MAX_NUMERIC_CHARTS]:
            values = pd.to_numeric(df[col], errors="coerce").dropna()
            if values.empty:
                continue
            fig = px.histogram(x=values, nbins=40, labels={"x": str(col), "y": "Records"})
            fig.update_traces(marker_color="#6C8AE4", opacity=0.88)
            add_figure(fig, f"Distribution: {col}", f"Histogram of {col}; useful for spotting skew, clusters, and unusual ranges.")

        if numeric_cols:
            selected = numeric_cols[:self.MAX_NUMERIC_CHARTS]
            melted = df[selected].melt(var_name="Column", value_name="Value")
            melted["Value"] = pd.to_numeric(melted["Value"], errors="coerce")
            melted = self._sample(melted.dropna(subset=["Value"]))
            if not melted.empty:
                fig = px.box(melted, x="Column", y="Value", points=False, color="Column")
                fig.update_layout(showlegend=False)
                add_figure(fig, "Numerical spread and potential outliers", "Box plots compare the range and spread of numeric fields. Scales may differ by column.")

        for col in categorical_cols[:self.MAX_CATEGORY_CHARTS]:
            values = df[col].astype("string").fillna("(Missing)")
            counts = values.value_counts().head(self.TOP_CATEGORIES).sort_values(ascending=True)
            if counts.empty:
                continue
            fig = px.bar(x=counts.values, y=counts.index.astype(str), orientation="h",
                         labels={"x": "Records", "y": str(col)})
            fig.update_traces(marker_color="#35A7A0")
            add_figure(fig, f"Most common values: {col}", f"Top {len(counts)} values in {col}; rare values are omitted from this chart.")

            pie_counts = values.value_counts().head(7)
            remaining = int(values.size - pie_counts.sum())
            labels = pie_counts.index.astype(str).tolist()
            vals = pie_counts.values.tolist()
            if remaining > 0:
                labels.append("Other / remaining")
                vals.append(remaining)
            pie = go.Figure(data=[go.Pie(labels=labels, values=vals, hole=0.32, textinfo="percent",
                                         hovertemplate="%{label}<br>%{value:,} records (%{percent})<extra></extra>")])
            add_figure(pie, f"Category share: {col}", "Share of the most common values; remaining values are grouped together.")

        if numeric_cols:
            for y_col in numeric_cols[:min(4, len(numeric_cols))]:
                if date_cols:
                    x_col = date_cols[0]
                    plot_df = df[[x_col, y_col]].copy()
                    plot_df[x_col] = pd.to_datetime(plot_df[x_col], errors="coerce")
                    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
                    plot_df = plot_df.dropna().sort_values(x_col)
                    plot_df = self._sample(plot_df)
                    x_values = plot_df[x_col]
                    x_title = str(x_col)
                else:
                    plot_df = self._sample(df[[y_col]].copy())
                    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
                    plot_df = plot_df.dropna(subset=[y_col])
                    x_values = plot_df.index
                    x_title = "Row index (sampled when large)"
                if plot_df.empty:
                    continue
                fig = go.Figure(go.Scatter(x=x_values, y=plot_df[y_col], mode="lines",
                                           name=str(y_col), line=dict(color="#E39A42", width=2), connectgaps=False))
                fig.update_layout(xaxis_title=x_title, yaxis_title=str(y_col), showlegend=False)
                add_figure(fig, f"Trend: {y_col}", "Shows how values change over time when a date field is detected; otherwise follows row order.")

        if len(numeric_cols) >= 2:
            corr_cols = numeric_cols[:20]
            corr = df[corr_cols].corr(numeric_only=True)
            fig = go.Figure(go.Heatmap(z=corr.values, x=[str(c) for c in corr.columns], y=[str(c) for c in corr.index],
                                       zmin=-1, zmax=1, colorscale="RdBu", reversescale=True,
                                       colorbar=dict(title="Correlation")))
            add_figure(fig, "Numerical correlation heatmap", "Correlation measures linear association, not causation. Only the first 20 numeric columns are shown.")

        if len(numeric_cols) >= 2:
            pair = self._sample(df[numeric_cols[:2]].copy()).dropna()
            if not pair.empty:
                fig = px.scatter(pair, x=numeric_cols[0], y=numeric_cols[1], opacity=0.65,
                                 labels={numeric_cols[0]: str(numeric_cols[0]), numeric_cols[1]: str(numeric_cols[1])})
                add_figure(fig, f"Relationship: {numeric_cols[0]} vs {numeric_cols[1]}", "A sampled scatter plot helps reveal association, clusters, and outliers.")

        missing = df.isna().sum().sort_values(ascending=False)
        missing = missing[missing > 0].head(30)
        if not missing.empty:
            fig = px.bar(x=missing.values, y=missing.index.astype(str), orientation="h",
                         labels={"x": "Missing cells", "y": "Column"})
            fig.update_traces(marker_color="#D96C75")
            add_figure(fig, "Missing values by column", "Columns with the most missing cells; only columns containing missing data are shown.")

        if not sections:
            sections.append("<section><p>No suitable charts could be generated from this dataset's column types.</p></section>")

        notes = []
        if len(numeric_cols) > self.MAX_NUMERIC_CHARTS:
            notes.append(f"Showing charts for the first {self.MAX_NUMERIC_CHARTS} of {len(numeric_cols)} numeric columns to keep the dashboard responsive.")
        if len(categorical_cols) > self.MAX_CATEGORY_CHARTS:
            notes.append(f"Showing charts for the first {self.MAX_CATEGORY_CHARTS} of {len(categorical_cols)} categorical columns to avoid an excessively long dashboard.")
        notes_html = "".join(f"<li>{note}</li>" for note in notes)
        html = f"""<!doctype html><html><head><meta charset='utf-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1'>
        <style>
        *{{box-sizing:border-box}} body{{margin:0;padding:22px;background:{bg};color:{fg};font-family:Arial,sans-serif}}
        h1{{margin:0 0 8px;font-size:28px}} .subtitle{{color:{muted};margin-bottom:20px}}
        .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:18px 0 24px}}
        .card{{background:{'#222735' if is_dark else '#F0EEE8'};border:1px solid {grid};border-radius:10px;padding:15px}}
        .card-label{{color:{muted};font-size:12px;margin-bottom:8px}} .card-value{{font-size:24px;font-weight:700}}
        section{{margin:18px 0 26px;padding:12px;background:{'#1D2230' if is_dark else '#FFFFFF'};border:1px solid {grid};border-radius:12px;overflow:hidden}}
        .description{{margin:3px 12px 0;color:{muted};font-size:13px;line-height:1.5}}
        .notes{{color:{muted};font-size:13px}} footer{{color:{muted};font-size:12px;margin:28px 0 8px}}
        </style></head><body>
        <h1>Automatic Data Exploration</h1>
        <div class='subtitle'>Generated automatically from the loaded dataset. No chart settings or column selection required.</div>
        <div class='cards'>{cards_html}</div>
        {('<ul class="notes">' + notes_html + '</ul>') if notes_html else ''}
        {''.join(sections)}
        <footer>Charts are exploratory summaries. Sampling and chart limits are used for responsiveness; all summary counts above are calculated from the loaded DataFrame.</footer>
        </body></html>"""
        self.chart_view.setHtml(html, QUrl("https://cdn.plot.ly/"))
