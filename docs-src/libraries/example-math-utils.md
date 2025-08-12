# example-math-utils

**Version:** 0.1.0

## Description

example-math-utils

Example math utilities library for demonstrating local development workflow

## Installation

Add to your application's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
example-math-utils = {path = "../libs/example-math-utils", develop = true}
```

## Usage

```python
from example_math_utils import add, multiply, divide, subtract
```

## API Reference

### Functions

#### add

```python
add(a: float, b: float) -> float
```

Add two numbers together.

This function demonstrates proper documentation and type hints
for shared library functions.

Args:
    a: The first number to add
    b: The second number to add

Returns:
    The sum of a and b

Example:
    >>> add(2, 3)
    5.0

#### multiply

```python
multiply(a: float, b: float) -> float
```

Multiply two numbers together.

Args:
    a: The first number to multiply
    b: The second number to multiply

Returns:
    The product of a and b

Example:
    >>> multiply(4, 5)
    20.0

#### divide

```python
divide(a: float, b: float) -> float
```

Divide the first number by the second number.

Args:
    a: The dividend
    b: The divisor

Returns:
    The quotient of a divided by b

Raises:
    ValueError: If divisor is zero

Example:
    >>> divide(10, 2)
    5.0

#### subtract

```python
subtract(a: float, b: float) -> float
```

Subtract the second number from the first number.

This function was added to demonstrate hot reloading!

Args:
    a: The minuend (number to subtract from)
    b: The subtrahend (number to subtract)

Returns:
    The difference of a minus b

Example:
    >>> subtract(10, 3)
    7.0

## Examples

### add

```python
>>> add(2, 3)
```

### multiply

```python
>>> multiply(4, 5)
```

### divide

```python
>>> divide(10, 2)
```

### subtract

```python
>>> subtract(10, 3)
```
