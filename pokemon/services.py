import requests
import random
from django.conf import settings
from .models import PokemonCard

class PokemonTCGService:
    """Service for interacting with the Pokémon TCG API"""
    
    def __init__(self):
        self.base_url = settings.POKEMON_TCG_API_BASE_URL
        self.api_key = settings.POKEMON_TCG_API_KEY
        self.headers = {
            'X-Api-Key': self.api_key
        } if self.api_key else {}
    
    def get_cards(self, page=1, page_size=20, **filters):
        """
        Fetch cards from the API with optional filters
        
        Args:
            page: Page number for pagination
            page_size: Number of cards per page
            **filters: Additional filters to apply (e.g., q="name:pikachu")
        
        Returns:
            dict: API response containing cards and pagination info
        """
        params = {
            'page': page,
            'pageSize': page_size,
            **filters
        }
        
        response = requests.get(
            f"{self.base_url}/cards",
            headers=self.headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def get_card_by_id(self, card_id):
        """
        Fetch a specific card by ID
        
        Args:
            card_id: The ID of the card to fetch
        
        Returns:
            dict: Card data
        """
        response = requests.get(
            f"{self.base_url}/cards/{card_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()['data']
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def get_random_cards(self, count=5, **filters):
        """
        Get a random selection of cards
        
        Args:
            count: Number of random cards to return
            **filters: Additional filters to apply
        
        Returns:
            list: List of random card data
        """
        # First, get the total count of cards matching the filters
        params = {
            'page': 1,
            'pageSize': 1,
            **filters
        }
        
        response = requests.get(
            f"{self.base_url}/cards",
            headers=self.headers,
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
        total_cards = response.json()['totalCount']
        
        if total_cards == 0:
            return []
        
        # Calculate how many pages we need to fetch
        page_size = min(250, total_cards)  # API max is 250 per page
        total_pages = (total_cards + page_size - 1) // page_size
        
        # Fetch a random page
        random_page = random.randint(1, total_pages)
        
        params = {
            'page': random_page,
            'pageSize': page_size,
            **filters
        }
        
        response = requests.get(
            f"{self.base_url}/cards",
            headers=self.headers,
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
        cards = response.json()['data']
        
        # Select random cards from the page
        if len(cards) <= count:
            return cards
        else:
            return random.sample(cards, count)
    
    def sync_card_to_db(self, card_data):
        """
        Sync a card from the API to the database
        
        Args:
            card_data: Card data from the API
        
        Returns:
            PokemonCard: The created or updated card object
        """
        card_id = card_data.get('id')
        
        # Check if card already exists
        try:
            card = PokemonCard.objects.get(card_id=card_id)
            # Update existing card
            for key, value in card_data.items():
                if hasattr(card, key) and key != 'id':
                    setattr(card, key, value)
            card.save()
            return card
        except PokemonCard.DoesNotExist:
            # Create new card
            card = PokemonCard(
                card_id=card_id,
                name=card_data.get('name', ''),
                set_name=card_data.get('set', {}).get('name', ''),
                set_code=card_data.get('set', {}).get('id', ''),
                rarity=card_data.get('rarity', ''),
                image_url=card_data.get('images', {}).get('small', ''),
                small_image_url=card_data.get('images', {}).get('small', ''),
                large_image_url=card_data.get('images', {}).get('large', ''),
                card_market_url=card_data.get('cardmarket', {}).get('url', ''),
                tcgplayer_url=card_data.get('tcgplayer', {}).get('url', ''),
                cardmarket_url=card_data.get('cardmarket', {}).get('url', ''),
                cardmarket_prices=card_data.get('cardmarket', {}).get('prices', {}),
                tcgplayer_prices=card_data.get('tcgplayer', {}).get('prices', {}),
                types=card_data.get('types', []),
                weaknesses=card_data.get('weaknesses', []),
                resistances=card_data.get('resistances', []),
                retreat_cost=card_data.get('retreatCost', []),
                converted_retreat_cost=card_data.get('convertedRetreatCost'),
                hp=card_data.get('hp', ''),
                artist=card_data.get('artist', ''),
                flavor_text=card_data.get('flavorText', ''),
                national_pokedex_numbers=card_data.get('nationalPokedexNumbers', []),
                legalities=card_data.get('legalities', {}),
                regulation_mark=card_data.get('regulationMark', ''),
                base_value=self._calculate_base_value(card_data)
            )
            card.save()
            return card
    
    def _calculate_base_value(self, card_data):
        """
        Calculate a base value for a card based on its attributes
        
        Args:
            card_data: Card data from the API
        
        Returns:
            int: Base value for the card
        """
        # Start with a base value
        value = 10
        
        # Adjust based on rarity
        rarity = card_data.get('rarity', '').lower()
        if 'rare' in rarity:
            value += 5
        if 'ultra' in rarity:
            value += 10
        if 'secret' in rarity:
            value += 15
        
        # Adjust based on HP
        hp = card_data.get('hp', '')
        if hp and hp.isdigit():
            hp_value = int(hp)
            if hp_value > 100:
                value += 5
        
        # Adjust based on converted retreat cost
        crc = card_data.get('convertedRetreatCost')
        if crc is not None:
            if crc == 0:
                value += 3  # No retreat cost is valuable
        
        # Adjust based on types (some types might be more valuable)
        types = card_data.get('types', [])
        if 'Dragon' in types:
            value += 5  # Dragon types are often valuable
        
        return value 