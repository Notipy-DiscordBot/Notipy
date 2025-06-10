function scrollToTop() {
    window.scrollTo({top: 0, behavior: 'smooth'});
}

window.addEventListener("DOMContentLoaded", () => {
    const cookieBanner = document.getElementById("cookie-banner");
    console.log("Checking cookie banner visibility: " + (document.cookie.indexOf("cookiesAccepted") === -1));
    if (document.cookie.indexOf("cookiesAccepted") === -1) {
        cookieBanner.style.display = "block";
    } else {
        cookieBanner.style.display = "none";
    }
});

window.addEventListener("scroll", () => {
    const btn = document.getElementById("scrollToTopBtn");
    if (window.scrollY > window.innerHeight * 0.5) {
        btn.classList.add("show");
    } else {
        btn.classList.remove("show");
    }

});

function hideCookieBanner() {
    document.getElementById("cookie-banner").style.display = "none";
}

async function acceptCookies() {
    try {
        const res = await fetch("/accept-cookies", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });

        if (!res.ok) throw new Error("Failed to accept cookies");

        const data = await res.json();

        if (data.success) {
            // 예: 배너 숨기고 페이지 새로고침 (선택)
            document.getElementById("cookieBanner").style.display = "none";
            location.reload(); // 또는 remove banner only
        }
    } catch (err) {
        console.error("Cookie acceptance failed:", err);
        alert("Something went wrong. Please try again.");
    }
    document.getElementById("cookie-banner").style.display = "none";
}
