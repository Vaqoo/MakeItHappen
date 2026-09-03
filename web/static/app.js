const $ = (id) => document.getElementById(id);

async function loadMe() {
  try {
    const response = await fetch('/api/me');
    const data = await response.json();
    if (!data.authenticated) return;
    const user = data.user;
    const login = document.querySelector('.login');
    login.textContent = 'Mein Discord-Profil';
    login.href = '#profile';
    const guildId = new URLSearchParams(location.search).get('guild');
    if (!guildId) return;
    const profileResponse = await fetch(`/api/profile/${guildId}/${user.id}`);
    if (!profileResponse.ok) return;
    renderProfile(await profileResponse.json(), user);
  } catch (error) {
    console.error('MIH profile load failed', error);
  }
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
  if (profile.banner_url) {
    $('banner').style.backgroundImage = `url("${profile.banner_url}")`;
    $('banner').style.backgroundSize = 'cover';
    $('banner').style.backgroundPosition = 'center';
  }
  const wins = $('wins');
  wins.innerHTML = '';
  if (!profile.wins.length) {
    wins.innerHTML = '<li>Deine nächsten Wins erscheinen hier.</li>';
    return;
  }
  profile.wins.forEach((win) => {
    const item = document.createElement('li');
    item.textContent = win.win;
    wins.appendChild(item);
  });
}

loadMe();
