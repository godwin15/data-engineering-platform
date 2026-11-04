
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.orc as orc

RAW_DIR = Path("data/raw")
BRONZE_DIR = Path("data/bronze")

TABLES = [
    "clients",
    "accounts",
    "portfolios",
    "securities",
    "holdings",
    "transactions",
    "trades",
    "advisors",
    "fees",
    "statements"
]


def convert_to_orc():
    total_files = 0
    total_records = 0

    for table_name in TABLES:
        csv_path = RAW_DIR / table_name / f"{table_name}.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"Missing file: {csv_path}")

        df = pd.read_csv(csv_path, dtype={
            "organisation_id": "string",
            "processing_date": "string"
        })

        # Check required partition columns
        required = {"organisation_id", "processing_date"}

        if not required.issubset(df.columns):
            raise ValueError(
                f"{table_name} is missing partition columns"
            )

        if df[list(required)].isna().any().any():
            raise ValueError(
                f"{table_name} contains null partition values"
            )

        table_files = 0
        table_records = 0

        # Partition by organization and processing date
        for (org_id, processing_date), partition in df.groupby(
            ["organisation_id", "processing_date"]
        ):
            output_dir = (
                BRONZE_DIR
                / table_name
                / f"organisation_id={org_id}"
                / f"processing_date={processing_date}"
            )

            output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / "data.orc"

            arrow_table = pa.Table.from_pandas(
                partition.reset_index(drop=True),
                preserve_index=False
            )

            orc.write_table(arrow_table, output_file)

            # Read back to verify the file
            verified = orc.ORCFile(output_file).read()

            assert verified.num_rows == len(partition), (
                f"Record mismatch in {output_file}"
            )

            table_files += 1
            table_records += len(partition)

        assert table_records == len(df), (
            f"Record mismatch in {table_name}"
        )

        total_files += table_files
        total_records += table_records

        print(
            f"{table_name}: {table_files} ORC files, "
            f"{table_records} records"
        )

    print("\nConversion completed successfully!")
    print(f"Total ORC files: {total_files}")
    print(f"Total records: {total_records}")


if __name__ == "__main__":
    convert_to_orc()
