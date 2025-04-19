# Younger Dryas Game

A turn-based survival simulation RPG set in the Younger Dryas period.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

From the project root directory:
```bash
python src/main.py
```

## Running Tests

```bash
pytest tests/
```

## Development

- The game uses Python 3.11+ and Pygame for rendering
- Main game loop is in `src/engine/core.py`
- Use `ESC` to exit the game 