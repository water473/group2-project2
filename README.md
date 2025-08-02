# PokeTrade - Pokémon Trading Card Platform

🌐 **Live Site**: [https://poketrade.pythonanywhere.com/](https://poketrade.pythonanywhere.com/)

A comprehensive Django web application for trading and collecting Pokémon cards. PokeTrade provides a complete ecosystem for Pokémon card enthusiasts to manage their collections, trade with other users, buy/sell cards in a marketplace, and communicate through an integrated messaging system.

## 🎯 Features

### Core Functionality
- **User Authentication & Profiles**: Complete user registration, login, and profile management with customizable avatars and bio
- **Pokémon Collection Management**: Build and manage your personal Pokémon card collection
- **Trading System**: Create and manage trade offers between users with real-time status tracking
- **Marketplace**: Buy and sell Pokémon cards using an in-game currency system
- **Messaging System**: Communicate with other traders through an integrated messaging platform
- **Wishlist**: Keep track of cards you want to acquire
- **Notification System**: Stay updated on trades, marketplace activities, and messages

### Technical Features
- **Responsive Design**: Modern, mobile-friendly interface
- **Real-time Updates**: Live status updates for trades and marketplace activities
- **Image Management**: Support for profile pictures and card images
- **Search & Filter**: Advanced search capabilities for cards and users
- **AI-Powered Descriptions**: OpenRouter API integration for generating dynamic Pokémon card descriptions
- **Admin Panel**: Comprehensive Django admin interface for platform management

## 🏗️ Architecture

### Django Apps
- **accounts**: User authentication, profiles, and notification preferences
- **pokemon**: Pokémon card data management and collection tracking
- **trading**: Trade offer creation, management, and history
- **marketplace**: Card buying/selling with transaction tracking
- **messaging**: User communication system

### Key Models
- **User & Profile**: Extended user model with coins, bio, and profile picture
- **PokemonCard**: Comprehensive card data from TCG API
- **UserPokemon**: User's personal card collection
- **TradeOffer**: Trade proposals between users
- **MarketplaceListing**: Card listings for sale
- **Message**: User communication system

## 📱 Usage

### For New Users
1. **Register**: Create an account to get started
2. **Complete Profile**: Add a profile picture and bio
3. **Explore Cards**: Browse available Pokémon cards
4. **Start Trading**: Create trade offers with other users
5. **Use Marketplace**: Buy and sell cards using in-game currency

### Key Features Walkthrough

#### Trading System
- Create trade offers by selecting cards from your collection
- Request cards from other users' collections
- Track trade status (pending, accepted, declined, completed)
- Receive notifications for trade updates

#### Marketplace
- List your cards for sale with custom pricing
- Browse available cards from other users
- Purchase cards using your coin balance
- Track transaction history

#### Collection Management
- Add cards to your personal collection
- Organize cards with nicknames and descriptions
- Mark favorite cards
- Generate AI-powered descriptions using OpenRouter API
- Track acquisition dates

#### Messaging
- Send direct messages to other users
- Discuss trades and marketplace transactions
- Archive and manage conversations

### API Integration
The platform integrates with multiple APIs:

- **Pokémon TCG API**: Fetches card data and images. Cards are automatically populated with real Pokémon card information.
- **OpenRouter API**: Powers AI-generated descriptions for Pokémon cards. Users can generate dynamic, engaging descriptions for their collection items using the DeepSeek model.

## 🙏 Acknowledgments

- Pokémon TCG API for card data
- Django community for the excellent framework
- Bootstrap for responsive design components

Built by Dimitrios, Eddie, James, and Omar
