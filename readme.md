# GaiaWeb


## Information

A tool to process test data to do GR&R easily.
Web app can be served from a Linux server

## Quickstart

``` bash
git clone git@gittf.ams-osram.info:os-opto-dev/source-codes/gaiaweb.git
pip install -r requirements.txt
cd grrd
python grrd/main.py
```

After starting the server, go to http://127.0.0.1:8051/gaiaweb



## Best practices: Create a new environment from scratch
``` bash
(base) ➜  grrdash git:(main) conda create -n py311 python=3.11
(base) ➜  grrdash git:(main) conda activate py311
(py311) ➜  grrdash git:(main) which python
/Users/jakelim/anaconda3/envs/py311/bin/python
(py311) ➜  grrdash git:(main) which pip
/Users/jakelim/anaconda3/envs/py311/bin/pip
(py311) ➜  grrdash git:(main) python -m pip install --upgrade pip
(py311) ➜  grrdash git:(main) python -m venv venv
(py311) ➜  grrdash git:(main) conda deactivate
(base) ➜  grrdash git:(main) conda deactivate

➜  grrdash git:(main) source ./venv/bin/activate
(venv) ➜  grrdash git:(main) which python
/Users/jakelim/SynologyDrive/cloud-active_project/grrdash/venv/bin/python
(venv) ➜  grrdash git:(main) which pip
/Users/jakelim/SynologyDrive/cloud-active_project/grrdash/venv/bin/pip


pip install tomlkit
pip install python-dotenv
pip install numpy
pip install pandas
pip install plotly
pip install dash

# (py311) ➜  grrdash git:(main) pip install -r requirements.txt
```

