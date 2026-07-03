
window.onload = function() {
    // انیمیشن درصد
    const scoreCards = document.querySelectorAll('.score-card .score-value');
    scoreCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.transform = 'scale(1.1)';
            card.style.transition = 'transform 0.3s ease';
        }, index * 100);
    });
};
