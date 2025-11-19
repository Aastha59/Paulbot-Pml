module.exports = {
  apps: [
    {
      name: "fastapi-backend",
      script: "cmd.exe",
      args: "/c python -m uvicorn app:app --host 0.0.0.0 --port 4047",
      cwd: "D:\\PROJECTS\\Paulbot-Pml",
      interpreter: "none", // prevents PM2 from forcing Node.js
      watch: true,          // auto-reload if files change
      autorestart: true,    // restart if crashed
      max_restarts: 5,      // prevent infinite crash loop
      env: {
        ENV: "production",
        PORT: 4047,
      },
    },
  ],
};
