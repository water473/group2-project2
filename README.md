# PokeTrade

PokeTrade is a web application where users can collect, trade, and manage Pokémon in a fun and interactive way. The platform allows users to sign up, receive randomly assigned Pokémon, exchange them with other players, and put them up for sale in a marketplace.

## Features

- **User Authentication**: Sign up, log in, and manage your profile
- **Pokémon Collection**: View and organize your Pokémon collection
- **Trading System**: Trade Pokémon with other users
- **Marketplace**: Buy and sell Pokémon
- **Messaging System**: Communicate with other users

## Tech Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite (development), PostgreSQL (production)
- **External APIs**: Pokémon API for Pokémon data

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://your-repository-url/poketrade.git
   cd poketrade
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser (admin):
   ```
   python manage.py createsuperuser
   ```

6. Load initial Pokémon data (if available):
   ```
   python manage.py load_pokemon_data
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

8. Open your browser and navigate to http://127.0.0.1:8000/

## Project Structure

- **accounts**: User authentication and profiles
- **pokemon**: Pokémon data and collection management
- **trading**: Trading system for exchanging Pokémon
- **marketplace**: Buy and sell Pokémon
- **messaging**: User-to-user communication

## Development Workflow

1. Create a new branch for each feature
2. Write tests for new functionality
3. Implement the feature
4. Submit a pull request for code review

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Pokémon and all related properties are owned by The Pokémon Company
- This is a fan project created for educational purposes 