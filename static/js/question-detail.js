
// دریافت زمان باقی‌مانده از قالب Django (این مقدار باید از ویو پاس داده شده باشد)
let secondsLeft = parseInt("{{ remaining_seconds|default:'0' }}");
  // اگر مقدار عددی است، سپس مقدار را چک کن
  if (isNaN(secondsLeft)) {
    secondsLeft = 0;  // در صورت نادرستی مقدار، صفر پذیرش می‌شود
  }

// دریافت عنصر نمایش تایمر
const timerElement = document.getElementById('timerDisplay');

// متغیرهایی برای مدیریت انتخاب کاربر
let selectedValue = null;
const selectedChoiceInput = document.getElementById('selectedChoice');
const submitChoiceInput = document.getElementById('submitChoice');

// ---- توابع مربوط به تایمر ----
function startTimer() {
    function tick() {
        // بررسی اینکه آیا زمان تمام شده است
        if (secondsLeft <= 0) {
            timerElement.innerHTML = '⏰ 00:00';
            // اگر زمان تمام شد، فرم را ارسال کن (به صورت خودکار)
            submitAnswer(); 
            return;
        }

        // محاسبه دقیقه و ثانیه برای نمایش
        const minutes = Math.floor(secondsLeft / 60);
        const seconds = secondsLeft % 60;
        
        // نمایش زمان در عنصر تایمر
        timerElement.innerHTML = `⏰ ${minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
        
        // تغییر رنگ تایمر در ۵ دقیقه آخر (۳۰۰ ثانیه)
        if (secondsLeft <= 300) {
            timerElement.style.color = '#e74c3c'; // قرمز برای هشدار
            timerElement.style.fontWeight = 'bold';
        } else {
            timerElement.style.color = ''; // رنگ پیش‌فرض
            timerElement.style.fontWeight = '';
        }

        // کاهش زمان باقی‌مانده
        secondsLeft--;
    }
    
    // اجرای تابع tick هر ۱ ثانیه
    setInterval(tick, 1000);
    
    // اجرای اولیه تابع tick برای نمایش زمان بلافاصله
    tick(); 
}

// ---- توابع مربوط به انتخاب گزینه ----
function selectOption(optionElement) {
    // حذف کلاس 'selected' از گزینه‌های قبلی
    document.querySelectorAll('.answer-option').forEach(opt => opt.classList.remove('selected'));
    // اضافه کردن کلاس 'selected' به گزینه انتخاب شده
    optionElement.classList.add('selected');
    
    // یافتن ورودی رادیویی درون گزینه
    const radioInput = optionElement.querySelector('input[type="radio"]');
    radioInput.checked = true; // فعال کردن رادیو باتن
    
    selectedValue = radioInput.value; // ذخیره مقدار انتخاب شده
    
    // به‌روزرسانی مقدار ورودی مخفی اول (برای فرم اصلی)
    selectedChoiceInput.value = selectedValue;
    // به‌روزرسانی مقدار ورودی مخفی دوم (برای فرم ارسال)
    submitChoiceInput.value = selectedValue; 
    
    console.log('✅ گزینه انتخاب شد:', selectedValue);
}

// تابع برای به‌روزرسانی ورودی مخفی در صورت انتخاب گزینه
function updateHiddenChoice(choiceId) {
    selectedValue = choiceId;
    selectedChoiceInput.value = choiceId;
    submitChoiceInput.value = choiceId;
    console.log('✅ مقدار انتخابی در ورودی مخفی ذخیره شد:', choiceId);
}

// ---- تابع ارسال پاسخ ----
// این تابع در رویداد onclick دکمه "بعدی" فراخوانی می‌شود
function submitAnswer() {
    // اگر گزینه‌ای انتخاب شده بود، مقدار آن را در ورودی مخفی قرار بده
    if (selectedValue) {
        submitChoiceInput.value = selectedValue;
        console.log('🚀 ارسال پاسخ:', selectedValue);
    } else {
        // اگر هیچ گزینه‌ای انتخاب نشده بود، ورودی مخفی را خالی بگذار (یا مقدار پیش‌فرض را بفرست)
        // این مطابق با "خالی هم OK" است
        submitChoiceInput.value = ''; 
        console.log('🚀 ارسال پاسخ خالی');
    }
    // اجازه بده فرم به صورت عادی ارسال شود
    return true; 
}

// ---- مقداردهی اولیه و راه‌اندازی ----

// به‌روزرسانی نوار پیشرفت (این مقدار را هم باید از ویو دریافت کنی)
// فعلا به صورت ثابت تنظیم شده، بهتر است از ویو پاس داده شود
const progressFill = document.getElementById('progressFill');
if (progressFill) {
    // فرض بر اینکه progress_percentage از ویو پاس داده شده است
    // progressFill.style.width = '{{ progress_percentage }}%'; 
    // یا یک مقدار ثابت برای تست:
     progressFill.style.width = '{{ progress_percentage }}%'; 
}


// راه‌اندازی تایمر پس از بارگذاری کامل صفحه
window.addEventListener('load', startTimer); 
