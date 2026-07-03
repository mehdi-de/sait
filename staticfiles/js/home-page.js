/*  مربوط به تبلیغات */
setTimeout(function() {
    document.getElementById('ad1')?.classList.add('show');
}, 5000);
setTimeout(function() {
    document.getElementById('ad2')?.classList.add('show');
}, 7000);

/*کدقسمت اسلایدهای تصاویر*/


document.addEventListener('DOMContentLoaded', function() {
    const slides = document.querySelectorAll('.slide');
    
    if (slides.length === 0) return;
    
    const nextBtn = document.querySelector('.next-btn');
    const prevBtn = document.querySelector('.prev-btn');
    const sliderContainer = document.querySelector('.slider-container');
    
    let currentSlide = 0;
    const slideInterval = 3000;  // ✅ 3 ثانیه
    let autoSliderInterval;

    function showSlide(index) {
        slides.forEach(slide => slide.classList.remove('active'));
        slides[index].classList.add('active');
    }

    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }

    function prevSlide() {
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        showSlide(currentSlide);
    }

    nextBtn.addEventListener('click', (e) => {
        e.preventDefault(); nextSlide(); resetAutoSlide();
    });
    prevBtn.addEventListener('click', (e) => {
        e.preventDefault(); prevSlide(); resetAutoSlide();
    });

    function startAutoSlide() {
        autoSliderInterval = setInterval(nextSlide, slideInterval);
    }

    function resetAutoSlide() {
        clearInterval(autoSliderInterval);
        startAutoSlide();
    }

    sliderContainer.addEventListener('mouseenter', () => clearInterval(autoSliderInterval));
    sliderContainer.addEventListener('mouseleave', startAutoSlide);

    showSlide(currentSlide);
    startAutoSlide();
});

// بستن بنر تبلیغ
function closeAd() {
    document.getElementById('ad-banner').classList.add('hidden');
    // 24 ساعت مخفی بمونه
    localStorage.setItem('adDismissed', 'true');
}

// چک کردن localStorage موقع لود
if (localStorage.getItem('adDismissed')) {
    document.getElementById('ad-banner').classList.add('hidden');
}
