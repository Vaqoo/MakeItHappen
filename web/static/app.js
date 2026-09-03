const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
let guildId = params.get('guild');

async function api(url, options = {}) {
  const response = await fetch(url, { credentials: 'same-origin', ...options });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function renderGuildPicker(guilds) {
  let picker = $('guild-picker');
  if (!picker) {
    picker = document.createElement('div');
    picker.id = 'guild-picker';
    picker.style.margin = '0 0 18px';
    const profile = $('profile');
    profile?.parentElement?.insertBefore(picker, profile);
  }
  picker.replaceChildren();
  if (!guilds.length) {
    const text = document.createElement('p');
    text.textContent = 'Du bist in keinem Discord-Server verfügbar, den MakeItHappen hier laden kann.';
    picker.appendChild(text);
    return;
  }
  const label = document.createElement('label');
  label.textContent = 'Server auswählen';
  label.style.display = 'block';
  label.style.marginBottom = '8px';
  label.style.fontWeight = '700';
  const select = document.createElement('select');
  select.id = 'guild-select';
  select.style.width = '100%';
  select.style.padding = '12px';
  select.style.borderRadius = '12px';
  select.style.background = 'rgba(255,255,255,.04)';
  select.style.color = 'inherit';
  select.style.border = '1px solid rgba(255,255,255,.12)';
  guilds.forEach((guild) => {
    const option = document.createElement('option');
    option.value = guild.id;
    option.textContent = guild.name;
    option.selected = guild.id === guildId;
    select.appendChild(option);
  });
  select.addEventListener('change', () => {
    const next = new URL(location.href);
    next.searchParams.set('guild', select.value);
    location.href = next.toString();
  });
  picker.append(label, select);
}

function renderProfile(profile, user) {
  const displayName = profile.display_name || user.global_name || user.username || 'MIH Member';
  $('name').textContent = displayName;
  $('title').textContent = profile.title || 'MakeItHappen Member';
  $('bio').textContent = profile.bio || 'Make it happen.';
  $('level').textContent = profile.level;
  $('xp').textContent = profile.xp;
  $('streak').textContent = profile.streak;
  $('coins').textContent = profile.coins;
  $('rank').textContent = `#${profile.rank}`;
  $('achievements').textContent = profile.achievements.length;
  $('progress').style.width = `${profile.level_progress}%`;
  $('progress-text').textContent = `${profile.level_progress} / 100 XP`;
  $('quote').textContent = profile.favorite_quote ? `“${profile.favorite_quote}”` : '“Make it happen.”';
  $('showcase').textContent = profile.showcase || 'Noch nichts ausgestellt.';
  $('avatar').textContent = displayName.slice(0, 1).toUpperCase();
  document.documentElement.dataset.color = profile.favorite_color || 'purple';
  if (profile.banner_url) {
    $('banner').style.backgroundImage = `url("${profile.banner_url}")`;
    $('banner').style.backgroundSize = 'cover';
    $('banner').style.backgroundPosition = 'center';
    $('banner').classList.add('custom-banner');
  }
  const wins = $('wins');
  wins.replaceChildren();
  if (!profile.wins.length) {
    const item = document.createElement('li');
    item.textContent = 'Deine nächsten Wins erscheinen hier.';
    wins.appendChild(item);
    return;
  }
  profile.wins.forEach((win) => {
    const item = document.createElement('li');
    item.textContent = win.win;
    wins.appendChild(item);
  });
}

async function loadMe() {
  const data = await api('/api/me');
  const login = document.querySelector('.login');
  if (!data.authenticated) {
    login.textContent = 'Login with Discord';
    login.href = '/auth/login';
    return;
  }
  const user = data.user;
  login.textContent = 'Mein Profil';
  login.href = '#profile';

  const guilds = await api('/api/my-guilds');
  if (!guildId && guilds.length) {
    guildId = guilds[0].id;
    const next = new URL(location.href);
    next.searchParams.set('guild', guildId);
    history.replaceState({}, '', next.toString());
  }
  renderGuildPicker(guilds);

  if (!guildId) {
    $('bio').textContent = 'Kein Discord-Server für dein Profil gefunden.';
    return;
  }
  try {
    renderProfile(await api(`/api/my-profile/${encodeURIComponent(guildId)}`), user);
    document.querySelector('.profile-edit').hidden = false;
  } catch (error) {
    console.error('MIH profile load failed', error);
    $('bio').textContent = 'Profil konnte nicht geladen werden.';
  }
}

function profilePayload() {
  return {
    display_name: $('edit-display-name').value,
    bio: $('edit-bio').value,
    favorite_quote: $('edit-quote').value,
    favorite_color: $('edit-color').value,
    title: $('edit-title').value,
    banner_url: $('edit-banner').value,
    showcase: $('edit-showcase').value,
  };
}

async function openEditor() {
  if (!guildId) return;
  const data = await api(`/api/my-profile/${encodeURIComponent(guildId)}`);
  $('edit-display-name').value = data.display_name || '';
  $('edit-bio').value = data.bio || '';
  $('edit-quote').value = data.favorite_quote || '';
  $('edit-color').value = data.favorite_color || 'purple';
  $('edit-title').value = data.title || '';
  $('edit-banner').value = data.banner_url || '';
  $('edit-showcase').value = data.showcase || '';
  $('editor').showModal();
}

document.querySelector('#edit-profile')?.addEventListener('click', openEditor);
document.querySelector('#editor-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    const profile = await api(`/api/my-profile/${encodeURIComponent(guildId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profilePayload()),
    });
    const me = await api('/api/me');
    renderProfile(profile, me.user);
    $('editor').close();
  } catch (error) {
    alert('Profil konnte nicht gespeichert werden.');
    console.error(error);
  } finally {
    button.disabled = false;
  }
});

document.querySelector('#logout')?.addEventListener('click', async () => {
  await fetch('/auth/logout', { method: 'POST', credentials: 'same-origin' });
  location.href = '/';
});

loadMe().catch(console.error);
