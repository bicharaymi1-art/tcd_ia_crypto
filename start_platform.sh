#!/data/data/com.termux/files/usr/bin/bash
cd ~/tcd_platform
tmux kill-session -t robot 2>/dev/null
tmux kill-session -t web 2>/dev/null
tmux new -d -s robot "python worker.py"
tmux new -d -s web "python web_app.py"
echo "Plateforme TCD CRYPTO AI TRADER (5 modules) démarrée !"
