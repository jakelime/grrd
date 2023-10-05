# GR&R tool with Dashboard

## Information

A tool to process test data to perform GR&R easily.
Web app can be served from a server.

## Quickstart

```bash
git clone git@github.com:jakelime/grrd.git
pip install -r requirements.txt
python grrd/main.py
```

After running the command from your `terminal`, your dashboard server is running.

Endpoints:

- Using your webbrowser on local machine (server), go to `http://127.0.0.1:8051/grrd/` to use the dashboard app
- On local machine (server), go to `http://0.0.0.0:8051/grrd/` -> This is to check if it works on your public facing ip-address
- Using a webbrowser on another machine (client), got to `http://X.X.X.X:8051/grrd/`, where `X.X.X.X` is the ip-address of the server

## Notes

- By default, this app is configured to be deployed using a subdomain `server.com/grrd/`
- This is facilitate deployment from using `nginx`, which you can simply configure directive for `/grrd`

## Math

For GR&R, we can use the MSA method which is defined by AIAG for the automotive industry

- https://www.aiag.org/quality/automotive-core-tools/msa
- https://www.spcforexcel.com/knowledge/measurement-systems-analysis/anova-gage-rr-part-1
- https://www.spcforexcel.com/knowledge/measurement-systems-analysis/anova-gage-rr-part-2

In GR&R, we are concerned with the variations of

- PARTS
- OPERATORS
- PARTS \* OPERATORS

In this customised implementation, we compile multiple (repeated tests) measurements on the same
DUT into statistical values (mean, std, range), breakdown by operators and create an interactive
`Operator_A vs Operator_Golden` plots for all operators.

The invidual plot of will have data visual presentation of all the essential details

- GR&R specs limits
- Production specs limits
- `Y vs X` of mean values `Operator_A vs Operator_Golden`
- Error bars signifying the range of each `PART`
- Correlation between the `Operator_A` and `Operator_Golden`, i.e. is
  `Operator_A` consistently poorer?

[Screenshot of webapp](images/screenshot01.png)

## Miscellaneous

### Create a new environment from scratch

```bash
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

```
