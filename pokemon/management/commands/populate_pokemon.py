from django.core.management.base import BaseCommand
from pokemon.services import PokemonTCGService
from pokemon.models import PokemonCard
import time

class Command(BaseCommand):
    help = 'Populates the database with Pokémon cards from the TCG API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of cards to fetch (default: 100)'
        )
        parser.add_argument(
            '--sets',
            type=str,
            default='sv3,sv4,sv5',
            help='Comma-separated list of set codes to fetch (default: sv3,sv4,sv5)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='Delay between API requests in seconds (default: 0.5)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        sets = options['sets'].split(',')
        delay = options['delay']
        
        service = PokemonTCGService()
        total_cards = 0
        
        self.stdout.write(self.style.SUCCESS(f'Starting to fetch cards from sets: {", ".join(sets)}'))
        
        for set_code in sets:
            if total_cards >= limit:
                break
                
            self.stdout.write(f'Fetching cards from set {set_code}...')
            
            try:
                # Get cards from this set
                response = service.get_cards(
                    page=1,
                    page_size=min(250, limit - total_cards),
                    q=f"set.id:{set_code}"
                )
                
                cards = response.get('data', [])
                total_in_set = response.get('totalCount', 0)
                
                self.stdout.write(f'Found {total_in_set} cards in set {set_code}')
                
                # Process each card
                for card_data in cards:
                    if total_cards >= limit:
                        break
                        
                    try:
                        card = service.sync_card_to_db(card_data)
                        total_cards += 1
                        self.stdout.write(f'Added/Updated card: {card.name} ({card.set_name})')
                        
                        # Respect rate limits
                        time.sleep(delay)
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error processing card: {str(e)}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error fetching set {set_code}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully processed {total_cards} cards')) 