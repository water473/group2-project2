// Main JavaScript file for PokeTrade

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
    
    // Collection filters
    const filterSelects = document.querySelectorAll('.collection-filter');
    if (filterSelects) {
        filterSelects.forEach(select => {
            select.addEventListener('change', function() {
                const filterType = this.getAttribute('data-filter-type');
                const filterValue = this.value;
                
                if (filterValue) {
                    window.location.href = `/pokemon/collection/filter/${filterType}/${filterValue}/`;
                }
            });
        });
    }
    
    // Collection sorting
    const sortSelect = document.getElementById('collection-sort');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const sortValue = this.value;
            if (sortValue) {
                window.location.href = `/pokemon/collection/sort/${sortValue}/`;
            }
        });
    }
    
    // Marketplace search
    const searchForm = document.getElementById('marketplace-search');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.getElementById('search-query').value;
            const type = document.getElementById('search-type').value;
            const rarity = document.getElementById('search-rarity').value;
            const minPrice = document.getElementById('search-min-price').value;
            const maxPrice = document.getElementById('search-max-price').value;
            
            let url = '/marketplace/search/?q=' + encodeURIComponent(query);
            if (type) url += '&type=' + encodeURIComponent(type);
            if (rarity) url += '&rarity=' + encodeURIComponent(rarity);
            if (minPrice) url += '&min_price=' + encodeURIComponent(minPrice);
            if (maxPrice) url += '&max_price=' + encodeURIComponent(maxPrice);
            
            window.location.href = url;
        });
    }
    
    // Trade offer item selection
    const tradeItemCheckboxes = document.querySelectorAll('.trade-item-checkbox');
    if (tradeItemCheckboxes) {
        tradeItemCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const pokemonId = this.value;
                const tradeItemsContainer = document.getElementById('selected-trade-items');
                
                if (this.checked) {
                    // Add to selected items
                    const pokemonName = this.getAttribute('data-pokemon-name');
                    const item = document.createElement('div');
                    item.classList.add('selected-trade-item');
                    item.id = 'selected-item-' + pokemonId;
                    item.innerHTML = `
                        <span>${pokemonName}</span>
                        <button type="button" class="btn-close btn-sm" data-pokemon-id="${pokemonId}"></button>
                        <input type="hidden" name="trade_items[]" value="${pokemonId}">
                    `;
                    tradeItemsContainer.appendChild(item);
                    
                    // Add event listener to remove button
                    item.querySelector('.btn-close').addEventListener('click', function() {
                        const pokemonId = this.getAttribute('data-pokemon-id');
                        document.getElementById('selected-item-' + pokemonId).remove();
                        document.querySelector(`.trade-item-checkbox[value="${pokemonId}"]`).checked = false;
                    });
                } else {
                    // Remove from selected items
                    document.getElementById('selected-item-' + pokemonId)?.remove();
                }
            });
        });
    }
}); 