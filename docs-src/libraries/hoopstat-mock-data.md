# hoopstat-mock-data

**Version:** 0.1.0

## Description

Mock NBA data generation framework for testing Hoopstat Haus data pipelines.

## Installation

Add to your application's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
hoopstat-mock-data = {path = "../libs/hoopstat-mock-data", develop = true}
```

## Usage

```python
from hoopstat_mock_data import MockDataGenerator, Team, Player, Game, PlayerStats, TeamStats
```

## API Reference

### Classes

#### Position

Basketball positions.

#### Conference

NBA conferences.

#### Division

NBA divisions.

#### GameType

Types of NBA games.

#### Team

NBA team model.

#### Player

NBA player model.

#### Game

NBA game model.

#### PlayerStats

Player statistics for a game.

#### TeamStats

Team statistics for a game.

### Functions

#### cli

```python
cli() -> Any
```

Mock NBA data generation framework for testing Hoopstat Haus data pipelines.

#### generate

```python
generate(teams: int, players_per_team: int, games: int, season: str, include_playoffs: bool, output: str, output_format: str, seed: Any, validate: bool, compress: bool) -> Any
```

Generate NBA mock data.

#### preset

```python
preset(preset: str, output: str, output_format: str, seed: Any) -> Any
```

Generate preset datasets for testing.

#### validate

```python
validate(filepath: str, data_type: Any) -> Any
```

Validate NBA data against schemas.

#### info

```python
info(filepath: str) -> Any
```

Show information about NBA data file.

#### main

```python
main() -> Any
```

Entry point for the CLI.
