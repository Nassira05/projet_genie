// Sélectionnez l'élément du menu déroulant
const dropdown = document.querySelector('.dropdown');

// Ajoutez un écouteur d'événement pour le clic
dropdown.addEventListener('click', function(event) {
    // Empêchez la propagation de l'événement pour éviter de fermer immédiatement le menu
    event.stopPropagation();

    // Sélectionnez le sous-menu déroulant
    const dropdownMenu = this.querySelector('.dropdown-menu');

    // Basculer la visibilité du sous-menu
    if (dropdownMenu.style.display === 'block') {
        dropdownMenu.style.display = 'none';
    } else {
        dropdownMenu.style.display = 'block';
    }
});

// Fermez le menu déroulant si l'utilisateur clique ailleurs sur la page
document.addEventListener('click', function() {
    const dropdownMenu = document.querySelector('.dropdown-menu');
    if (dropdownMenu.style.display === 'block') {
        dropdownMenu.style.display = 'none';
    }
});