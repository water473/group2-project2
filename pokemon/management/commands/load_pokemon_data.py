import requests
import random
from django.core.management.base import BaseCommand
from pokemon.models import Pokemon

class Command(BaseCommand):
    help = 'Load Pokemon data from the PokeAPI'

    def handle(self, *args, **options):
        self.stdout.write('Loading Pokemon data...')
        
        # Define how many Pokemon to load
        pokemon_count = 50  # Limit for demonstration purposes
        
        # Define rarity distribution
        rarities = {
            'common': 50,      # 50% chance
            'uncommon': 30,    # 30% chance
            'rare': 15,        # 15% chance
            'ultra_rare': 4,   # 4% chance
            'legendary': 1,    # 1% chance
        }
        
        # Load Pokemon from the API
        for i in range(1, pokemon_count + 1):
            try:
                # Get Pokemon data from the API
                response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{i}')
                if response.status_code == 200:
                    pokemon_data = response.json()
                    
                    # Get additional data for the description
                    species_response = requests.get(pokemon_data['species']['url'])
                    species_data = species_response.json()
                    
                    # Extract English description
                    description = ""
                    if species_data.get('flavor_text_entries'):
                        for entry in species_data['flavor_text_entries']:
                            if entry.get('language', {}).get('name') == 'en':
                                description = entry['flavor_text'].replace('\n', ' ').replace('\f', ' ')
                                break
                    
                    # Determine types
                    types = pokemon_data['types']
                    primary_type = types[0]['type']['name']
                    secondary_type = types[1]['type']['name'] if len(types) > 1 else None
                    
                    # Randomly assign rarity based on distribution
                    rarity = random.choices(
                        list(rarities.keys()),
                        weights=list(rarities.values()),
                        k=1
                    )[0]
                    
                    # Determine base value based on rarity
                    base_values = {
                        'common': random.randint(50, 100),
                        'uncommon': random.randint(100, 300),
                        'rare': random.randint(300, 700),
                        'ultra_rare': random.randint(700, 1500),
                        'legendary': random.randint(1500, 3000),
                    }
                    base_value = base_values[rarity]
                    
                    # Create Pokemon object in the database
                    pokemon, created = Pokemon.objects.update_or_create(
                        pokemon_id=pokemon_data['id'],
                        defaults={
                            'name': pokemon_data['name'].capitalize(),
                            'image_url': pokemon_data['sprites']['other']['official-artwork']['front_default'],
                            'primary_type': primary_type,
                            'secondary_type': secondary_type,
                            'rarity': rarity,
                            'base_value': base_value,
                            'description': description,
                            'height': pokemon_data['height'] / 10,  # Convert to meters
                            'weight': pokemon_data['weight'] / 10,  # Convert to kg
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Added Pokemon: {pokemon.name}'))
                    else:
                        self.stdout.write(f'Updated Pokemon: {pokemon.name}')
                
                else:
                    self.stdout.write(self.style.WARNING(f'Failed to fetch Pokemon #{i}: {response.status_code}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing Pokemon #{i}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {Pokemon.objects.count()} Pokemon')) 