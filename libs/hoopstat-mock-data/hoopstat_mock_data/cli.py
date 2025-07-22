"""Command-line interface for the mock NBA data generator."""

from pathlib import Path

import click

from .exporters.json_exporter import JSONExporter
from .exporters.parquet_exporter import ParquetExporter
from .generators.mock_data_generator import MockDataGenerator
from .validators.schema_validator import SchemaValidator


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Mock NBA data generation framework for testing Hoopstat Haus data pipelines."""
    pass


@cli.command()
@click.option("--teams", default=30, help="Number of teams to generate (max 30)")
@click.option("--players-per-team", default=15, help="Number of players per team")
@click.option("--games", default=100, help="Number of games to generate")
@click.option("--season", default="2023-24", help="Season string (e.g., '2023-24')")
@click.option("--include-playoffs", is_flag=True, help="Include playoff games")
@click.option("--output", required=True, help="Output file path")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "parquet"]),
    default="json",
    help="Output format",
)
@click.option("--seed", type=int, help="Random seed for reproducible generation")
@click.option("--validate", is_flag=True, help="Validate generated data")
@click.option("--compress", is_flag=True, help="Use compression (for Parquet)")
def generate(
    teams: int,
    players_per_team: int,
    games: int,
    season: str,
    include_playoffs: bool,
    output: str,
    output_format: str,
    seed: int | None,
    validate: bool,
    compress: bool,
):
    """Generate NBA mock data."""
    click.echo(f"Generating NBA mock data with seed={seed}")

    # Initialize generator
    generator = MockDataGenerator(seed=seed)

    # Generate data
    try:
        dataset = generator.generate_complete_dataset(
            num_teams=teams,
            players_per_team=players_per_team,
            num_games=games,
            season=season,
            include_playoffs=include_playoffs,
        )

        click.echo("Generated:")
        click.echo(f"  - {len(dataset['teams'])} teams")
        click.echo(f"  - {len(dataset['players'])} players")
        click.echo(f"  - {len(dataset['games'])} games")
        click.echo(f"  - {len(dataset['player_stats'])} player stats")
        click.echo(f"  - {len(dataset['team_stats'])} team stats")

        # Validate if requested
        if validate:
            click.echo("Validating generated data...")
            # Convert models to dicts for validation
            dict_dataset = {}
            for key, models in dataset.items():
                dict_dataset[key] = [model.model_dump() for model in models]

            report = SchemaValidator.generate_validation_report(dict_dataset)

            if report["overall_valid"]:
                click.echo("✓ Data validation passed")
            else:
                click.echo("✗ Data validation failed:")
                for validation_type, results in report.items():
                    if (
                        isinstance(results, dict)
                        and "errors" in results
                        and results["errors"]
                    ):
                        click.echo(f"  {validation_type}: {results['errors']}")
                return

        # Export data
        output_path = Path(output)

        if output_format == "json":
            JSONExporter.export_to_file(dataset, output_path)
            click.echo(f"✓ Data exported to {output_path}")

        elif output_format == "parquet":
            if output_path.suffix.lower() == ".parquet":
                # Single file - export largest table
                largest_table = max(dataset.items(), key=lambda x: len(x[1]))
                compression = "snappy" if compress else None
                ParquetExporter.export_to_file(
                    largest_table[1], output_path, compression
                )
                click.echo(f"✓ {largest_table[0]} data exported to {output_path}")
            else:
                # Directory - export all tables
                compression = "snappy" if compress else None
                ParquetExporter.export_multiple_tables(
                    dataset, output_path, compression
                )
                click.echo(f"✓ All tables exported to {output_path}/")

    except Exception as e:
        click.echo(f"✗ Error generating data: {e}")
        raise click.Abort()


@cli.command()
@click.option(
    "--preset",
    type=click.Choice(["small", "medium", "large"]),
    default="small",
    help="Preset dataset size",
)
@click.option("--output", required=True, help="Output file path")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "parquet"]),
    default="json",
    help="Output format",
)
@click.option("--seed", type=int, help="Random seed for reproducible generation")
def preset(preset: str, output: str, output_format: str, seed: int | None):
    """Generate preset datasets for testing."""
    click.echo(f"Generating {preset} preset dataset with seed={seed}")

    generator = MockDataGenerator(seed=seed)

    if preset == "small":
        dataset = generator.generate_small_test_dataset()
    elif preset == "medium":
        dataset = generator.generate_medium_test_dataset()
    elif preset == "large":
        dataset = generator.generate_large_simulation_dataset()

    click.echo(f"Generated {preset} dataset:")
    click.echo(f"  - {len(dataset['teams'])} teams")
    click.echo(f"  - {len(dataset['players'])} players")
    click.echo(f"  - {len(dataset['games'])} games")

    # Export data
    output_path = Path(output)

    if output_format == "json":
        JSONExporter.export_to_file(dataset, output_path)
    elif output_format == "parquet":
        if output_path.suffix.lower() == ".parquet":
            # Export largest table
            largest_table = max(dataset.items(), key=lambda x: len(x[1]))
            ParquetExporter.export_to_file(largest_table[1], output_path)
        else:
            # Export all tables
            ParquetExporter.export_multiple_tables(dataset, output_path)

    click.echo(f"✓ Data exported to {output_path}")


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--data-type", help="Specific data type to validate (teams, players, etc.)"
)
def validate(filepath: str, data_type: str | None):
    """Validate NBA data against schemas."""
    click.echo(f"Validating data in {filepath}")

    try:
        # Load data
        path = Path(filepath)
        if path.suffix.lower() == ".json":
            data = JSONExporter.load_from_file(path)
        elif path.suffix.lower() == ".parquet":
            df = ParquetExporter.load_from_file(path)
            data = df.to_dict("records")
        else:
            click.echo("✗ Unsupported file format. Use .json or .parquet")
            return

        # Validate
        if data_type:
            valid, errors = SchemaValidator.validate_data(data, data_type)
            if valid:
                click.echo(f"✓ {data_type} data validation passed")
            else:
                click.echo(f"✗ {data_type} data validation failed:")
                for error in errors:
                    click.echo(f"  {error}")
        else:
            # Validate complete dataset
            if isinstance(data, dict):
                report = SchemaValidator.generate_validation_report(data)

                click.echo("Validation Report:")
                click.echo(f"  Overall Valid: {report['overall_valid']}")

                for validation_type, results in report.items():
                    if isinstance(results, dict) and "valid" in results:
                        status = "✓" if results["valid"] else "✗"
                        click.echo(f"  {validation_type}: {status}")
                        if "errors" in results and results["errors"]:
                            for error_type, error_list in results["errors"].items():
                                if error_list:
                                    click.echo(
                                        f"    {error_type}: {len(error_list)} errors"
                                    )
            else:
                click.echo("✗ Data format not supported for complete validation")

    except Exception as e:
        click.echo(f"✗ Error validating data: {e}")


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
def info(filepath: str):
    """Show information about NBA data file."""
    click.echo(f"File: {filepath}")

    try:
        path = Path(filepath)

        if path.suffix.lower() == ".json":
            data = JSONExporter.load_from_file(path)

            if isinstance(data, dict):
                click.echo("Data types:")
                for key, value in data.items():
                    if isinstance(value, list):
                        click.echo(f"  {key}: {len(value)} items")
            elif isinstance(data, list):
                click.echo(f"List with {len(data)} items")

            file_size = path.stat().st_size
            click.echo(f"File size: {file_size:,} bytes")

        elif path.suffix.lower() == ".parquet":
            df = ParquetExporter.load_from_file(path)

            click.echo(f"Shape: {df.shape}")
            click.echo(f"Columns: {list(df.columns)}")
            click.echo(f"Memory usage: {df.memory_usage(deep=True).sum():,} bytes")

            file_size = path.stat().st_size
            click.echo(f"File size: {file_size:,} bytes")

    except Exception as e:
        click.echo(f"✗ Error reading file: {e}")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
