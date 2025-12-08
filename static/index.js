
document.addEventListener("DOMContentLoaded", () => {
  var sound = new Howl({
    src: ['/static/ring.mp3']
  });

  const ring = () => {
    sound.play()
  }



  document.getElementById("room-name").addEventListener("input", (e) => {
    window.history.replaceState({}, "", `/${btoa(e.target.value)}`);
  });
  document.getElementById("copy-link").addEventListener("click", (e) => {
    navigator.clipboard.writeText(window.location.href);

    e.target.textContent = "Copied!";

    setTimeout(() => {
      e.target.textContent = "Copy Link to Doorbell";

    }, 4000)

  });
  document.getElementById("doorbell").addEventListener("click", () => {
    ring();
  })
});
