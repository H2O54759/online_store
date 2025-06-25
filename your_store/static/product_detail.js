document.addEventListener('DOMContentLoaded', function() {
    var carouselElement = document.getElementById('productCarousel');
    if (!carouselElement) return;

    var carousel = bootstrap.Carousel.getOrCreateInstance(carouselElement);

    var buttons = document.querySelectorAll('[data-carousel-index]');
    buttons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var index = parseInt(btn.getAttribute('data-carousel-index'), 10);
            carousel.to(index);
        });
    });
});
