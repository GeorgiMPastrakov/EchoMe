(function(){
  const btn  = document.getElementById('themeToggle');
  if(!btn) return;
  const sun  = document.getElementById('iconSun');
  const moon = document.getElementById('iconMoon');
  const apply = () => {
    const dark = document.documentElement.classList.contains('dark');
    sun.style.display = dark ? 'inline' : 'none';
    moon.style.display = dark ? 'none'  : 'inline';
  };
  btn.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    apply();
  });
  apply();
})(); 