const sections = document.querySelectorAll('.section');
const dotNav = document.querySelector('.dot-nav');
let current = 0;

// dot 생성 및 클릭 이벤트 바인딩
sections.forEach((_, i) => {
    const dot = document.createElement('div');
    dot.classList.add('dot');
    if (i === 0) dot.classList.add('active');
    dot.addEventListener('click', (e) => {
        e.stopPropagation();  // 🔒 클릭 이벤트 상위로 전파되지 않도록 차단
        const direction = i > current ? 1 : -1;
        showSection(i, direction);
    });
    dotNav.appendChild(dot);
});

function updateDots() {
    document.querySelectorAll('.dot').forEach((dot, i) => {
        dot.classList.toggle('active', i === current);
    });
}

function showSection(next, direction) {
    if (next < 0 || next >= sections.length || next === current) return;
    if (typeof direction !== 'number') direction = next > current ? 1 : -1;

    const currentSection = sections[current];
    const nextSection = sections[next];

    currentSection.style.transition = 'transform 0.6s ease, opacity 0.6s ease';
    nextSection.style.transition = 'none';
    nextSection.style.transform = `translateX(${100 * direction}vw)`;
    nextSection.style.opacity = '0';
    nextSection.classList.add('active');

    requestAnimationFrame(() => {
        nextSection.style.transition = 'transform 0.6s ease, opacity 0.6s ease';
        currentSection.style.transform = `translateX(${-100 * direction}vw)`;
        currentSection.style.opacity = '0';
        currentSection.classList.remove('active');

        nextSection.style.transform = 'translateX(0)';
        nextSection.style.opacity = '1';
    });

    current = next;
    updateDots();
}

// ✅ dot-nav 제외 영역에서만 페이지 전환 가능
document.body.addEventListener('click', (e) => {
    // dot-nav 영역 내 클릭이면 무시
    if (e.target.closest('.dot-nav')) return;

    const x = e.clientX;
    const middle = window.innerWidth * 0.4;
    if (x < middle) {
        showSection(current - 1, -1);
    } else {
        showSection(current + 1, 1);
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const lang = window.location.pathname.split("/")[1] || "en"; // ex: /ko/case → 'ko', 기본 'en'
    const images = document.querySelectorAll("img[data-id]");

    images.forEach(img => {
        const imageName = img.getAttribute("data-id");
        img.src = `/static/img/${lang}/${imageName}`;
    });
});