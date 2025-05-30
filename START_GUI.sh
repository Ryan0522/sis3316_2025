tmux new-session -s sis3316 -d
tmux split-window -v 
tmux split-window -v 
tmux split-window -v 
tmux select-layout tiled
tmux send-keys -t 0 "source venv/bin/activate && cat welcome.txt" ENTER
tmux send-keys -t 1 "source venv/bin/activate" ENTER
tmux send-keys -t 1 "python livePlotter.py" ENTER
tmux send-keys -t 2 "source venv/bin/activate" ENTER 
tmux send-keys -t 2 "python sis3316_gui.py &" ENTER
tmux send-keys -t 2 "htop" ENTER
tmux send-keys -t 3 "source venv/bin/activate" ENTER
tmux send-keys -t 3 "python readoutServer.py" ENTER
tmux select-pane -t 0
tmux attach-session
