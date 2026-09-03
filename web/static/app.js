const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const guildId = params.get('guild');

async function api(url, options = {}) {
  const response = await fetch(url, { credentials: 'same-origin', ...options });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
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
  if (!guildId) {
    $('bio').textContent = 'Füge ?guild=DEINE_SERVER_ID an die URL an, um dein Server-Profil zu laden.';
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
