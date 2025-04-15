from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from pokemon.models import UserPokemon
from pokemon.services import PokemonTCGService
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_user_pokemon_collection(sender, instance, created, **kwargs):
    """
    Signal handler to create a collection of random Pokémon cards for new users
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new user
        **kwargs: Additional arguments
    """
    logger.info(f"Signal triggered for user {instance.username}, created: {created}")
    
    if created:
        # Only create collection for new users
        logger.info(f"Creating starter collection for user {instance.username}")
        service = PokemonTCGService()
        
        # Get 5 random cards for the new user
        try:
            # Try to get some common cards first
            logger.info("Fetching common cards...")
            common_cards = service.get_random_cards(
                count=3,
                q="rarity:Common"
            )
            logger.info(f"Found {len(common_cards)} common cards")
            
            # Then get some uncommon cards
            logger.info("Fetching uncommon cards...")
            uncommon_cards = service.get_random_cards(
                count=2,
                q="rarity:Uncommon"
            )
            logger.info(f"Found {len(uncommon_cards)} uncommon cards")
            
            # Get one double rare card
            logger.info("Fetching double rare card...")
            rare_cards = service.get_random_cards(
                count=1,
                q="rarity:Rare"
            )
            logger.info(f"Found {len(rare_cards)} double rare card")
            
            # Combine the cards
            random_cards = common_cards + uncommon_cards + rare_cards
            logger.info(f"Total cards to assign: {len(random_cards)}")
            
            # Add each card to the user's collection
            for card_data in random_cards:
                # Sync the card to our database
                card = service.sync_card_to_db(card_data)
                logger.info(f"Synced card: {card.name}")
                
                # Create the user's Pokémon entry
                UserPokemon.objects.create(
                    user=instance,
                    card=card
                )
                logger.info(f"Added {card.name} to user's collection")
                
        except Exception as e:
            # Log the error but don't prevent user creation
            logger.error(f"Error creating Pokémon collection for user {instance.username}: {str(e)}")
            logger.exception("Full traceback:") 