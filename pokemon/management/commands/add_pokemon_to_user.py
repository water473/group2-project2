from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pokemon.models import Pokemon, UserPokemon, PokemonCard
import random
from django.utils import timezone
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Adds multiple Pokémon to a user\'s collection'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to add Pokémon to')
        parser.add_argument('--count', type=int, default=10, help='Number of Pokémon to add (default: 10)')
        parser.add_argument('--rarity', type=str, help='Filter by rarity (common, uncommon, rare, ultra_rare, legendary)')
        parser.add_argument('--type', type=str, help='Filter by type')

    def handle(self, *args, **options):
        username = options['username']
        count = options['count']
        rarity = options['rarity']
        pokemon_type = options['type']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
            return

        # Get all available cards
        cards = list(PokemonCard.objects.all())
        
        # Apply filters if specified
        if rarity:
            cards = [card for card in cards if card.rarity == rarity]
        if pokemon_type:
            cards = [card for card in cards if pokemon_type in (card.types or [])]

        if not cards:
            self.stdout.write(self.style.ERROR('No Pokémon cards found matching the criteria'))
            return

        # Get existing cards for this user
        existing_card_ids = set(UserPokemon.objects.filter(user=user).values_list('card_id', flat=True))
        
        # Filter out cards the user already has
        available_cards = [card for card in cards if card.id not in existing_card_ids]

        if not available_cards:
            self.stdout.write(self.style.ERROR('No new Pokémon cards available to add'))
            return

        # Add specified number of random cards to user's collection
        added_count = 0
        skipped_count = 0
        max_attempts = min(count * 2, len(available_cards) * 2)  # Avoid infinite loop
        attempts = 0

        while added_count < count and attempts < max_attempts and available_cards:
            # Get a random card
            card = random.choice(available_cards)
            
            try:
                # Create UserPokemon entry
                UserPokemon.objects.create(
                    user=user,
                    card=card,
                    acquired_date=timezone.now()
                )
                added_count += 1
                available_cards.remove(card)  # Remove card from available pool
            except IntegrityError:
                skipped_count += 1
                available_cards.remove(card)  # Remove card that caused error
            
            attempts += 1

        # Prepare status message
        status = f'Successfully added {added_count} Pokémon to {username}\'s collection'
        if skipped_count > 0:
            status += f' ({skipped_count} duplicates skipped)'
        if added_count < count:
            status += f'\nNote: Could only add {added_count} out of {count} requested Pokémon'
            if not available_cards:
                status += ' (no more unique cards available)'

        self.stdout.write(self.style.SUCCESS(status)) 