"""Human-readable CLI for querying Hoopstat Haus NBA statistics."""

import asyncio
import json
import sys

import click

from app.http_client import ArtifactFetchError, get_client


@click.group()
def cli():
    """Hoopstat Haus -- NBA statistics from the command line."""


@cli.command("get-index")
def get_index():
    """Fetch the latest data index listing available datasets."""
    client = get_client()
    try:
        raw = asyncio.run(client.fetch_index())
    except ArtifactFetchError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    data = json.loads(raw)
    click.echo(json.dumps(data, indent=2))


@cli.command("get-artifact")
@click.argument("resource_uri")
def get_artifact(resource_uri: str):
    """Fetch a specific JSON artifact by its resource URI.

    RESOURCE_URI is the path to the artifact, for example:

    \b
      player_daily/2024-11-15/2544
      team_daily/2024-11-15/1610612747
      top_lists/2024-11-15/points
    """
    client = get_client()
    try:
        raw = asyncio.run(client.fetch_artifact(resource_uri))
    except ArtifactFetchError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    data = json.loads(raw)
    click.echo(json.dumps(data, indent=2))
