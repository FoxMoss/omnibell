document.addEventListener("DOMContentLoaded", () => {
  var sound = new Howl({ src: ["/static/ring.mp3"] });

  let ring_counter = 0;
  const updateRings = () => {
    document.getElementById("rings").innerHTML =
      `Doorbell has been rung ${ring_counter} times.`;
  };
  const ring = (message) => {
    sound.play();
    ring_counter++;
    updateRings();
    if (message !== undefined) {
      let div = document.createElement("div");
      div.innerText = message;
      document.getElementById("logs").appendChild(div);
      document.getElementById("logs").scrollTo(document.getElementById("logs").scrollHeight, 0);
    }
  };

  let connection;

  const openCallback = () => {
    connection.send(
      JSON.stringify({
        type: "listen_to_door",
        door: document.getElementById("room-name").value,
      }),
    );
  };

  const messageCallback = (event) => {
    const eventData = JSON.parse(event.data);
    if (eventData["type"] == "ring") {
      ring(eventData["message"]);
    }
    if (eventData["type"] == "door_info") {
      ring_counter = eventData["times_rang"];
      updateRings();
      for (let message in eventData["messages"]) {
        let div = document.createElement("div");
        div.innerText = message;
        document.getElementById("logs").appendChild(div);
      document.getElementById("logs").scrollTo(document.getElementById("logs").scrollHeight, 0);
      }
    }
  };

  const closeCallback = () => {
    setTimeout(() => {
      connection = new WebSocket("/connect");
      connection.addEventListener("open", openCallback);
      connection.addEventListener("message", messageCallback);
      connection.addEventListener("close", closeCallback);
    }, 1000);
  };

  connection = new WebSocket("/connect");
  connection.addEventListener("open", openCallback);
  connection.addEventListener("message", messageCallback);
  connection.addEventListener("close", closeCallback);

  document.getElementById("room-name").addEventListener("input", (e) => {
    connection.send(
      JSON.stringify({
        type: "listen_to_door",
        door: document.getElementById("room-name").value,
      }),
    );
    window.history.replaceState({}, "", `/${btoa(e.target.value)}`);
  });
  document.getElementById("copy-link").addEventListener("click", (e) => {
    navigator.clipboard.writeText(window.location.href);

    e.target.textContent = "Copied!";

    setTimeout(() => {
      e.target.textContent = "Copy Link to Doorbell";
    }, 4000);
  });
  document.getElementById("doorbell").addEventListener("click", () => {
    const ringVal =
      document.getElementById("message").value == ""
        ? undefined
        : document.getElementById("message").value;
    connection.send(
      JSON.stringify({
        type: "ring",
        door: document.getElementById("room-name").value,
        message: ringVal,
      }),
    );
    ring(ringVal);
    document.getElementById("message").value = "";
  });
});
