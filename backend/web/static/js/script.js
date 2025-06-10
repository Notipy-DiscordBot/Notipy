// 📘 script.js — 모달 및 FAQ 인터랙션 처리

// 🔘 관리자 모달이 열린 상태인지 저장
let adminModalOpened = false;

// 🧩 관리자 아이콘 클릭 시 모달 열기
// 모달을 표시하고 약간의 지연 후 외부 클릭 감지를 활성화
document.querySelector(".admin-icon").addEventListener("click", () => {
    const modal = document.getElementById("admin-modal");
    modal.style.display = "flex";

    // 외부 클릭 감지를 잠깐 뒤에 활성화 (열자마자 닫히는 걸 방지)
    setTimeout(() => {
        adminModalOpened = true;
    }, 10);
});

// 📴 모달 외부 클릭 시 모달 닫기
document.addEventListener("click", function (event) {
    const modal = document.getElementById("admin-modal");
    const modalContent = document.getElementById("admin-modal-content");

    if (!modal || modal.style.display !== "flex" || !adminModalOpened) return;
    
    // 모달 영역 바깥 클릭 감지
    if (!modalContent.contains(event.target)) {
        modal.style.display = "none";
        adminModalOpened = false;
    }
});

// ❓ FAQ 클릭 시 답변 토글 동작
// 각 FAQ 항목 클릭 시 답변 표시/숨김 처리
document.querySelectorAll(".faq li").forEach(item => {
  item.addEventListener("click", () => {
    const answerBox = item.querySelector(".faq-answer");
    const answer = item.dataset.answer;

    // 답변이 숨겨져 있으면 표시, 이미 표시되어 있으면 숨김
    if (answerBox.style.display === "none") {
      answerBox.textContent = answer;
      answerBox.style.display = "block";
    } else {
      answerBox.style.display = "none";
    }
  });
});

