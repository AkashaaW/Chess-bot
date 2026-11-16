# \# Chess Bot

# 

# A desktop chess game built with Python, Pygame, and python-chess. You play White against a computer opponent with three difficulty settings.

# 

# \## Run on Windows

# 

# Open PowerShell in the project folder and run:

# 

# ```powershell

# py -m pip install pygame python-chess

# py main.py

# ```

# 

# \## How to play

# 

# 1\. Choose \*\*Easy\*\*, \*\*Medium\*\*, or \*\*Hard\*\*, then click \*\*Start\*\*.

# 2\. Click a white piece to see its legal moves. Click a highlighted square to move there. The bot plays Black.

# 3\. Use \*\*Pause\*\* to resume, restart at the same difficulty, or return to the main menu.

# 4\. After a win, loss, or draw, choose \*\*New Game\*\* to play again at the same difficulty or \*\*Main Menu\*\* to change difficulty.

# 

# \## Scoreboard

# 

# Open \*\*Scoreboard\*\* from the main menu to see your previous games, including the date, difficulty, and result. A win earns 1 point, a draw earns 0.5, and a loss earns 0. The game saves completed results in a local `scores.json` file so they are available the next time you open it.

# 

# \## Project files

# 

# | File or folder | Purpose |

# | --- | --- |

# | `main.py` | Pygame window, menus, and game loop |

# | `bot.py` | Computer opponent and difficulty settings |

# | `scores.py` | Saves and loads completed game results |

# | `Images/` | Chess piece PNGs |

# 

