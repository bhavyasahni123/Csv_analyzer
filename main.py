
import pandas as pd


def load_dataset(file_path):
    """Load a CSV file into a DataFrame."""
    return pd.read_csv(file_path)


def show_overview(df):
    print("\nDataset Overview ")
    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])
    print("Total cells:", df.size)
    print(
        "Memory usage (bytes):",
        df.memory_usage(deep=True).sum()
    )


def show_missing_values(df):
    print("\nMissing Values Report  ")

    missing_count = df.isnull().sum()

    if len(df) > 0:
        missing_percent = (
            missing_count / len(df) * 100
        ).round(2)
    else:
        missing_percent = pd.Series(
            0.0, index=df.columns
        )

    summary = pd.DataFrame({
        "Data Type": df.dtypes.astype(str),
        "Missing Count": missing_count,
        "Missing Percent": missing_percent,
    })

    print(summary)


def show_numerical_statistics(df):
    print("\n Numerical Statistics  ")

    numerical_columns = df.select_dtypes(
        include="number"
    )

    if numerical_columns.empty:
        print("No numerical columns found.")
        return

    print(numerical_columns.describe())


def show_categorical_statistics(df):
    print("\n  Categorical Statistics  ")

    categorical_columns = df.select_dtypes(
        include=["object", "string", "category"]
    )

    if categorical_columns.empty:
        print("No categorical columns found.")
        return

    print(categorical_columns.describe())


def show_category_frequencies(df, limit=10):
    print("\n  Categorical Frequency Analysis  ")

    categorical_columns = df.select_dtypes(
        include=["object", "string", "category"]
    ).columns

    if len(categorical_columns) == 0:
        print("No categorical columns found.")
        return

    for column in categorical_columns:
        print(f"\n{column} — Top {limit} values:")
        print(df[column].value_counts().head(limit))


def show_column_details(df):
    print("\n  Column Details  ")

    for column in df.columns:
        print(f"\nColumn: {column}")
        print("Data type:", df[column].dtype)
        print("Unique values:", df[column].nunique())
        print("Missing values:", df[column].isna().sum())


def select_columns(df, selected_columns=None):
    """Show statistics for selected columns.

    If selected_columns is omitted, ask for column names
    through the terminal.
    """
    print("\n  Available Columns  ")

    for column in df.columns:
        print(column)

    if selected_columns is None:
        selected = input(
            "\nEnter column names separated by commas: "
        )

        selected_columns = [
            column.strip()
            for column in selected.split(",")
            if column.strip()
        ]

    if not selected_columns:
        print("Please select at least one column.")
        return

    invalid_columns = [
        column
        for column in selected_columns
        if column not in df.columns
    ]

    if invalid_columns:
        print("Invalid columns:", invalid_columns)
        return

    print("\n  Selected Column Details  ")
    print(df[selected_columns].describe(include="all"))
