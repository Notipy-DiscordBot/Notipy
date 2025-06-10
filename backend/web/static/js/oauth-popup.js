function handleDiscordAuthSuccess(innerHTML) {
    const parentOrigin = "https://notipy.code0987.com";

    if (window.opener) {
        // 부모 창에게 인증 성공 메시지 전송
        window.opener.postMessage("discord-auth-success", parentOrigin);

        // 0.5초 후 자동으로 팝업 닫기
        setTimeout(() => {
            window.close();
        }, 500);
    } else {
        // 팝업이 아닌 단독 실행된 경우 사용자에게 안내
        // document.body.innerHTML = "<p>이 페이지는 인증 완료 후 자동으로 닫힙니다.<br> 만일 닫히지 않을 경우 직접 창을 닫아주세요.</p>";
        document.body.innerHTML = innerHTML;
        console.log("팝업이 아닌 단독 실행된 경우입니다. 창을 닫아주세요.");
    }
};