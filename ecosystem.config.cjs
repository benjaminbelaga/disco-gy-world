module.exports = {
  apps: [{
    name: 'discoworld-api',
    cwd: '/var/www/world.yoyaku.io',
    script: 'python3',
    args: '-m uvicorn packages.api.main:app --host 127.0.0.1 --port 8200',
    interpreter: 'none',
    env: {
      DISCOWORLD_DATA: '/var/www/world.yoyaku.io/data',
      DISCOWORLD_DB: '/var/www/world.yoyaku.io/data/discoworld.db',
      DISCOWORLD_USERS_DB: '/var/www/world.yoyaku.io/data/discoworld_users.db',
    },
    max_restarts: 10,
    restart_delay: 5000,
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
  }]
};
