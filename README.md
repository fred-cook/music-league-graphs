# music-league-graphs

This repo is intended to scrape data from downloaded music league results pages.

## Usage (non programmers)

Currently usage for non-programmers will be tricky, in future I'll try and have it generate the graphs and save them to a folder, but for now you'll have to be a bit more involved.

Clone this directory. You will need [`uv`](https://github.com/astral-sh/uv) installed to run the code. The easiest way is with `pip install uv`, however there are other options listed [here](https://github.com/astral-sh/uv?tab=readme-ov-file#installation). Once `uv` is installed navigate to the directory in a terminal and run `uv sync`. This will install the required python version and modules in a virtual environment.

Go to every results page in your music league and download (using ctrl-s) to a folder. The full saved file is needed, otherwise all of the results won't appear.

You will then need to open an editor (e.g. vs code) and modify the filepath in stats.ipynb to the folder you created above. Hopefully vscode will automatically use the venv created in the `uv` steps above, you can press run all at the top of the interactive notebook and Bob's your uncle it will run.
