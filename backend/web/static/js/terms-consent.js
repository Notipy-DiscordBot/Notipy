// ✅ 약관 영역 및 버튼 요소 참조
const termsBox = document.getElementById('terms-box');
const agreeCheckbox = document.getElementById('agree-check');
const agreeButton = document.getElementById('agree-button');
const warningText = document.getElementById('warning-text');

let scrolledToBottom = false;

// 1️⃣ 스크롤 확인
termsBox.addEventListener('scroll', () => {
    if (termsBox.scrollTop + termsBox.clientHeight >= termsBox.scrollHeight - 5) {
        scrolledToBottom = true;
        warningText.style.display = 'none';
        if (agreeCheckbox.checked) {
            agreeButton.disabled = false;
        }
    }
});

// 2️⃣ 체크박스 클릭 시 조건 검사
function toggleButton() {
    if (!scrolledToBottom && agreeCheckbox.checked) {
        // 체크 해제 및 경고
        agreeCheckbox.checked = false;
        warningText.style.display = 'block';
        agreeButton.disabled = true;
        return;
    }

    warningText.style.display = 'none';
    agreeButton.disabled = !(agreeCheckbox.checked && scrolledToBottom);
}

// 3️⃣ 버튼 클릭 시 디스코드 인증 팝업 띄우기
agreeButton.onclick = () => {
    const width = 600;
    const height = 800;
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;

    const popup = window.open(
        "https://discord.com/oauth2/authorize?client_id=955999346321686609&permissions=8&response_type=code&redirect_uri=https%3A%2F%2Fnotipy.code0987.com%2Foauth-popup&integration_type=0&scope=bot+identify",
        "discordOAuth",
        `width=${width},height=${height},top=${top},left=${left}`
    );

    if (!popup) {
        alert("팝업 차단을 해제해주세요!");
    }
};

// 4️⃣ 팝업으로부터 인증 성공 메시지 수신 → oauth-success.html 이동
window.addEventListener("message", (event) => {
    console.log("✅ 메시지 수신:", event.origin, event.data);
    if (event.origin !== "https://notipy.code0987.com") return;
    if (event.data === "discord-auth-success") {
        window.location.href = "/oauth-success";
    }
});