document.addEventListener("DOMContentLoaded", () => {
    const lang = window.location.pathname.split("/")[1] || "en"; // ex: /ko/case → 'ko', 기본 'en'
    const images = document.querySelectorAll("img[data-id]");

    images.forEach(img => {
        const imageName = img.getAttribute("data-id");
        if (imageName) {
            img.src = `/static/img/${lang}/${imageName}`;
        }
    });
});