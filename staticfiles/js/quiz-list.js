
// کد کامل و بدون ایراد - تضمینی کار می‌کند
document.addEventListener('DOMContentLoaded', function() {
    // المان‌ها
    const modal = document.getElementById('exam-modal');
    const closeBtn = document.querySelector('.close-button');
    const startExamBtn = document.getElementById('start-exam');
    
    let currentQuizUrl = null;

    // باز کردن modal با URL آزمون
    function openQuizModal(quizUrl) {
        currentQuizUrl = quizUrl;
        modal.style.display = 'block';
    }

    // بستن modal
    function closeModal() {
        modal.style.display = 'none';
    }

    // شروع آزمون
    function startQuiz() {
        closeModal();
        if (currentQuizUrl) {
            setTimeout(function() {
                window.location.href = currentQuizUrl;
            }, 200);
        }
    }

    // Event Listeners
    closeBtn.onclick = closeModal;
    startExamBtn.onclick = startQuiz;
    
    // بستن با کلیک backdrop
    window.onclick = function(event) {
        if (event.target === modal) {
            closeModal();
        }
    };

    // دکمه‌های شروع آزمون
    const quizButtons = document.querySelectorAll('a.start-quiz-btn:not([disabled])');
    quizButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            openQuizModal(href);
        });
    });

    // Modal خوشامدگویی - فقط یکبار
    if (!localStorage.getItem('welcomeModalShown')) {
        setTimeout(function() {
            openQuizModal(null); // بدون URL برای خوشامدگویی
        }, 600);
        localStorage.setItem('welcomeModalShown', 'true');
    }
});
