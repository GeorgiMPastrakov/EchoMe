export async function recordAudio(ms=3000){
  const stream = await navigator.mediaDevices.getUserMedia({audio:true});
  const rec = new MediaRecorder(stream);
  const chunks=[];
  rec.ondataavailable=e=>chunks.push(e.data);
  rec.start();
  await new Promise(r=>setTimeout(r,ms));
  rec.stop();
  await new Promise(r=>rec.onstop=r);
  stream.getTracks().forEach(t=>t.stop());
  return new Blob(chunks,{type:'audio/wav'});
}
