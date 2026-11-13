
/* =========================================
   آزمون‌یار | Home Page JavaScript
   Optimized Version
========================================= */

document.addEventListener('DOMContentLoaded', function () {

    /* =====================================
       1. تبلیغات
    ===================================== */

    const ad1 = document.getElementById('ad1');
    const ad2 = document.getElementById('ad2');

    if (ad1) {
        setTimeout(() => {
            if (ad1.isConnected) {
                ad1.classList.add('show');
            }
        }, 5000);
    }

    if (ad2) {
        setTimeout(() => {
            if (ad2.isConnected) {
                ad2.classList.add('show');
            }
        }, 7000);
    }


    /* =====================================
       2. اسلایدر صفحه اصلی
    ===================================== */

    const slider = document.querySelector('.ay-slider');

    if (!slider) return;

    const slides = Array.from(
        slider.querySelectorAll('.ay-slide')
    );

    if (slides.length === 0) return;

    const nextBtn = document.querySelector('.ay-next');
    const prevBtn = document.querySelector('.ay-prev');
    const dotsContainer = document.querySelector('.ay-slider-dots');

    const slideInterval = 3000;

    let currentSlide = Math.max(
        0,
        slides.findIndex(slide => slide.classList.contains('is-active'))
    );

    let autoSlideTimer = null;

    let isPaused = false;


    /* نمایش اسلاید */

    function showSlide(index) {

        currentSlide = (index + slides.length) % slides.length;

        slides.forEach((slide, i) => {

            const isActive = i === currentSlide;

            slide.classList.toggle('is-active', isActive);

            slide.setAttribute(
                'aria-hidden',
                String(!isActive)
            );

        });

        if (dotsContainer) {

            const dots = dotsContainer.querySelectorAll('button');

            dots.forEach((dot, i) => {

                dot.classList.toggle(
                    'is-active',
                    i === currentSlide
                );

                dot.setAttribute(
                    'aria-current',
                    i === currentSlide ? 'true' : 'false'
                );

            });

        }

    }


    /* ساخت دکمه‌های نقطه‌ای */

    if (dotsContainer && slides.length > 1) {

        dotsContainer.innerHTML = '';

        slides.forEach((slide, index) => {

            const dot = document.createElement('button');

            dot.type = 'button';

            dot.className = 'ay-slider-dot';

            dot.setAttribute(
                'aria-label',
                `رفتن به اسلاید ${index + 1}`
            );

            dot.addEventListener('click', function () {

                showSlide(index);

                resetAutoSlide();

            });

            dotsContainer.appendChild(dot);

        });

    }


    /* حرکت به اسلاید بعدی */

    function nextSlide() {

        showSlide(currentSlide + 1);

    }


    /* حرکت به اسلاید قبلی */

    function prevSlide() {

        showSlide(currentSlide - 1);

    }


    /* مدیریت تایمر */

    function stopAutoSlide() {

        if (autoSlideTimer !== null) {

            clearInterval(autoSlideTimer);

            autoSlideTimer = null;

        }

    }


    function startAutoSlide() {

        stopAutoSlide();

        if (
            slides.length < 2 ||
            isPaused ||
            document.hidden
        ) {
            return;
        }

        autoSlideTimer = setInterval(
            nextSlide,
            slideInterval
        );

    }


    function resetAutoSlide() {

        stopAutoSlide();

        startAutoSlide();

    }


    /* دکمه بعدی */

    if (nextBtn) {

        nextBtn.addEventListener('click', function (event) {

            event.preventDefault();

            nextSlide();

            resetAutoSlide();

        });

    }


    /* دکمه قبلی */

    if (prevBtn) {

        prevBtn.addEventListener('click', function (event) {

            event.preventDefault();

            prevSlide();

            resetAutoSlide();

        });

    }


    /* توقف هنگام قرار گرفتن موس */

    slider.addEventListener('mouseenter', function () {

        isPaused = true;

        stopAutoSlide();

    });


    slider.addEventListener('mouseleave', function () {

        isPaused = false;

        startAutoSlide();

    });


    /* توقف هنگام فوکوس صفحه‌کلید */

    slider.addEventListener('focusin', function () {

        isPaused = true;

        stopAutoSlide();

    });


    slider.addEventListener('focusout', function (event) {

        if (!slider.contains(event.relatedTarget)) {

            isPaused = false;

            startAutoSlide();

        }

    });


    /* توقف هنگام مخفی شدن تب مرورگر */

    document.addEventListener('visibilitychange', function () {

        if (document.hidden) {

            stopAutoSlide();

        } else {

            startAutoSlide();

        }

    });


    /* اجرای اولیه */

    showSlide(currentSlide);

    startAutoSlide();

});
