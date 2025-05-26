const tabs = document.querySelectorAll('.tabBtn');
const sections = {
  profile:    document.getElementById('profileTab'),
  'add-voice':document.getElementById('addVoiceTab'),
  generate:   document.getElementById('generateTab')
};

function activate(tab) {
  tabs.forEach(b => b.classList.toggle('border-indigo-600', b.dataset.tab===tab));
  Object.entries(sections).forEach(([k,el]) => el.hidden = k !== tab);
  if (tab === 'profile') loadProfile();
  if (tab === 'add-voice') mountAddVoice();
  if (tab === 'generate') mountGenerate();
}
tabs.forEach(b => b.addEventListener('click', () => activate(b.dataset.tab)));
activate('profile');

function headers(extra={}) { return { Authorization:`Bearer ${getToken()}`, ...extra }; }
async function api(url, opts={}) {
  const r = await fetch(url, {...opts, headers: headers(opts.headers)});
  if (!r.ok) throw Error(await r.text());
  return r.json();
}

async function loadProfile() {
  const el = sections.profile;
  el.innerHTML = '<p>Loading…</p>';
  try {
    const me   = await api('/api/users/me');
    const list = await api('/api/voices');
    el.innerHTML = `
      <h3 class="text-xl font-semibold">${me.name}</h3>
      <h4 class="text-lg mt-4 mb-2">My Voices</h4>
      <ul class="space-y-2">
        ${list.map(v=>`
          <li class="p-3 border rounded flex justify-between items-center">
            <span>${v.name}</span>
            <audio controls src="${v.url}" class="ml-4"></audio>
          </li>`).join('')}
      </ul>`;
  } catch(e){ el.innerHTML = `<p class="text-red-500">${e}</p>`; }
}

function mountAddVoice() {
  const el = sections['add-voice'];
  if (el.dataset.ready) return;
  el.dataset.ready='1';
  el.innerHTML = `
    <form id="voiceUpload" class="space-y-4">
      <input name="name" class="w-full border p-2 rounded" placeholder="Voice label" required>
      <input name="file" type="file" accept="audio/*" class="w-full" required>
      <button class="px-4 py-2 bg-indigo-600 text-white rounded">Upload</button>
    </form>`;
  el.querySelector('#voiceUpload').addEventListener('submit', async e=>{
    e.preventDefault();
    const fd = new FormData(e.target);
    const res = await fetch('/api/voices/upload', {method:'POST', headers:headers(), body:fd});
    res.ok ? (alert('Uploaded!'), loadProfile()) : alert('Upload failed');
  });
}
async function mountGenerate() {
  const el = sections.generate;
  if (el.dataset.ready) return;
  el.dataset.ready='1';
  const voices = await api('/api/voices');
  el.innerHTML = `
    <form id="genForm" class="space-y-4 max-w-md">
      <select name="voice_id" class="w-full border p-2 rounded">
        ${voices.map(v=>`<option value="${v.id}">${v.name}</option>`).join('')}
      </select>
      <textarea name="text" rows="4" placeholder="Enter text…" class="w-full border p-2 rounded" required></textarea>
      <button class="px-4 py-2 bg-indigo-600 text-white rounded">Generate</button>
    </form>
    <div id="genResult" class="mt-6"></div>`;
  el.querySelector('#genForm').addEventListener('submit', async e=>{
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.target).entries());
    const res = await fetch('/api/speech', {
      method:'POST',
      headers:headers({'Content-Type':'application/json'}),
      body:JSON.stringify(body)
    });
    if (res.ok){
      const {url} = await res.json();
      document.getElementById('genResult').innerHTML =
        `<audio controls src="${url}" class="w-full"></audio>
         <a href="${url}" download class="underline ml-2">Download</a>`;
    } else alert('Generation failed');
  });
}
