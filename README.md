# AGH Bot

Telegram bot designed for the AGH University of Science and Technology community. Features captcha verification to
prevent spam and anecdote sending to keep the community engaged.

## Installation

0. Ensure [Docker](https://docs.docker.com/engine/install/) and
   [Docker Compose](https://docs.docker.com/compose/install/) are installed.
1. Clone and navigate to the repository:

    ```shell
    git clone https://github.com/nikijaz/agh-bot.git
    cd agh-bot/
    ```

2. Create `.env` file with your secrets. You can use `.env.example` as a template.
3. Modify `config.toml` with your bot configuration.
4. Create `anecdotes.txt` file with anecdotes, each separated by "`***`".
5. Run detached Docker containers:

    ```shell
    docker compose up -d
    ```

## Development

0. Ensure [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/)
   and [uv](https://docs.astral.sh/uv/getting-started/installation/) are installed.
1. Clone and navigate to the repository:

    ```shell
    git clone https://github.com/nikijaz/agh-bot.git
    cd agh-bot/
    ```

2. Create `.env` file with your secrets. You can use `.env.example` as a template.
3. Modify `config.toml` with your bot configuration.
4. Create `anecdotes.txt` file with anecdotes, each separated by "`***`".
5. Install dependencies:

    ```shell
    uv sync
    ```

6. Make changes to the code.

7. Verify your changes by running the bot:

    ```shell
    uv run main.py
    ```

8. Check for any typing, linting or formatting issues:

    ```shell
    mypy .
    ruff check .
    ruff format --check .
    ```

## Technologies Used

**Python** powers the bot's logic, with **uv** as the package manager. The bot uses the **Aiogram** library for Telegram
API communication. **PostgreSQL** serves as the database, with **peewee** for ORM. **Docker** is used for
containerization.
