# AGH Bot

Telegram bot designed for the AGH University of Science and Technology
community. Features captcha verification to prevent spam and anecdote sending to
keep the community engaged.

## Installation

0. Ensure [Docker](https://docs.docker.com/engine/install/) and [Docker
   Compose](https://docs.docker.com/compose/install/) are installed.
1. Clone and navigate to the repository:

    ```shell
    git clone https://github.com/nikijaz/agh-bot.git
    cd agh-bot/
    ```

2. Create `.env` file with your configuration. You can use `.env.example` as a
   template.
3. Create `anecdotes.txt` file with anecdotes, each separated by "`***`".
4. Run compose in production mode:

    ```shell
    docker compose -f docker-compose.prod.yml up -d
    ```

## Development

0. Ensure [Docker](https://docs.docker.com/engine/install/) and [Docker
   Compose](https://docs.docker.com/compose/install/) are installed.
1. Clone and navigate to the repository:

    ```shell
    git clone https://github.com/nikijaz/agh-bot.git
    cd agh-bot/
    ```

2. Create `.env` file with your configuration. You can use `.env.example` as a
   template.
3. Create `anecdotes.txt` file with anecdotes, each separated by "`***`".

4. Run compose in development mode:

    ```shell
    docker compose -f docker-compose.dev.yml up
    ```

5. Make changes to the codebase. The bot will automatically reload.
6. Check for any typing, linting or formatting issues:

    ```shell
    mypy .
    ruff check .
    ruff format --check .
    ```

## Technologies Used

**Python** powers the bot's logic, with **uv** as the package manager. The bot
uses the **Aiogram** library for Telegram API communication. **PostgreSQL**
serves as the database, with **peewee** for ORM. **Docker** is used for
containerization.
