function toggleSession(sessionId, action) {
    fetch("/toggle-session/" + sessionId + "/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: new URLSearchParams({
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        }
    });
}

// 🔄 Auto refresh for students every 10 seconds
document.addEventListener("DOMContentLoaded", function () {

    const container = document.querySelector(".container");
    const isStaff = container.dataset.staff === "True";
    const isActive = container.dataset.active === "True";

    if (!isStaff && !isActive) {
        setInterval(function () {
            window.location.reload();
        }, 10000);
    }
});


document.addEventListener("DOMContentLoaded", function () {
    const bars = document.querySelectorAll(".progress-bar");
    bars.forEach(function(bar) {
        const percent = bar.dataset.progress;
        if (percent) {
            bar.style.width = percent + "%";
        }
    });
});