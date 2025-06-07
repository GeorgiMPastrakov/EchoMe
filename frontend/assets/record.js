// microphone recording & upload
let mediaRecorder, recordedChunks = [];
const recordBtn = document.getElementById("recordBtn");
const stopBtn   = document.getElementById("stopBtn");
const labelIn   = document.getElementById("recordLabel");

async function initRecorder() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);

  mediaRecorder.ondataavailable = e => {
    if (e.data.size) recordedChunks.push(e.data);
  };

  mediaRecorder.onstop = async () => {
    const blob = new Blob(recordedChunks, { type: "audio/wav" });
    recordedChunks = [];

    const fd = new FormData();
    fd.append("file" , blob              , "record.wav");
    fd.append("label", labelIn.value || "Unnamed");

    const res = await fetch("/api/voices/record", {
      method : "POST",
      headers: { Authorization: "Bearer " + localStorage.getItem("token") },
      body   : fd
    });

    alert(res.ok ? "Voice saved!" : "Upload failed");
  };
}

recordBtn?.addEventListener("click", async () => {
  if (!mediaRecorder) await initRecorder();
  mediaRecorder.start();
  recordBtn.disabled = true;
  stopBtn.disabled   = false;
});

stopBtn?.addEventListener("click", () => {
  mediaRecorder.stop();
  recordBtn.disabled = false;
  stopBtn.disabled   = true;
});
