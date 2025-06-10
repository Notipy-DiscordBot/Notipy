function toggleLangPopup() {
    const popup = document.getElementById('lang-popup');
    if (!popup) return;
    popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
}

async function switchLang(lang) {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    const path = window.location.pathname;
    const curfile = path.split('/').pop() || 'index';

    if (getCookie("cookiesAccepted") === "true") {
        try {
            const response = await fetch("/api/web/lang", {
                method: "POST",
                headers: {
                    "Content-Type": "text/plain"  // ✅ 중요
                },
                body: lang  // ✅ JSON.stringify({ lang }) 아님
            });

            if (response.ok) {
                window.location.href = `/${lang}/${curfile}`;
            } else {
                console.error("Language change failed:", response.status);
            }
        } catch (error) {
            console.error("Request error:", error);
        }
    } else {
        window.location.href = `/${lang}/${curfile}`;
    }
}



document.addEventListener('click', function (event) {
    const popup = document.getElementById('lang-popup');
    const btn = document.getElementById('lang-btn');
    if (!popup || !btn) return;
    if (!popup.contains(event.target) && event.target !== btn) {
        popup.style.display = 'none';
    }
});
