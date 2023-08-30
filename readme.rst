================================================================
MSAG - MSA GRR tool
================================================================

Measurement Systems Analysis `MSA <https://www.spcforexcel.com/knowledge/measurement-systems-analysis/acceptance-criteria-for-MSA>`_.

Gage repeatability and reproducibility (GRR)


Information
================================================================

Math, formula, details and explanations

- https://www.spcforexcel.com/knowledge/measurement-systems-analysis/anova-gage-rr-part-1
- https://www.spcforexcel.com/knowledge/measurement-systems-analysis/anova-gage-rr-part-2

Automotive Industry Action Group (AIAG) Standards for the use of MSA

- https://www.aiag.org/quality/automotive-core-tools/msa




Using ``git``
================================================================

Read the full guide here: `git & ssh helper <https://gittf.ams-osram.info/jake.lim/ssh-keys-helper>`_.



Installation and Setup
================================================================

Always, always run python using a virutal environment.

In this project, we will be using the in-built python venv, pip and python 3.10.


Windows
----------------------------------------------------------------

.. code-block:: powershell

    U:\>cd /d %userprofile%
    C:\Users\jli8>cd C:\_pythonWork\msa-grr

    C:\_pythonWork\msa-grr>where python
    C:\Users\jli8\AppData\Local\Programs\Python\Python311\python.exe
    C:\Users\jli8\AppData\Local\Microsoft\WindowsApps\python.exe
    C:\_pythonWork\msa-grr>python --version
    Python 3.11.2
    C:\_pythonWork\msa-grr>python -m venv venv
    
    C:\_pythonWork\msa-grr>venv\Scripts\activate    
    (venv) C:\_pythonWork\msa-grr>where python
    C:\_pythonWork\msa-grr\venv\Scripts\python.exe
    C:\Users\jli8\AppData\Local\Programs\Python\Python311\python.exe
    C:\Users\jli8\AppData\Local\Microsoft\WindowsApps\python.exe    
    (venv) C:\_pythonWork\msa-grr>python -c "import os, sys; print(os.path.dirname(sys.executable))"
    C:\_pythonWork\msa-grr\venv\Scripts    
    (venv) C:\_pythonWork\msa-grr>python --version
    Python 3.11.2


.. code-block:: text

    python.exe -m pip install --upgrade pip
    pip install tomlkit natsort python-dotenv
    pip install pandas matplotlib seaborn
    pip install plotly dash dash_bootstrap_components
    .. pip install notebook voila pygwalker 
    pip install SQLAlchemy==1.4.46
    pip install mariadb
    pip install pyarrow openpyxl customtkinter pypdf
    pip install GageRnR
    pip install pyinstaller
    pip freeze > requirements-win.txt

    pyinstaller cli.py --windowed --noconfirm --name msag --icon="icon.ico" --add-data "bundles/*;bundles/" --hidden-import mariadb --hidden-import sqlalchemy --collect-all pyarrow --add-data "C:/_pythonWork/msa-grr/venv/Lib/site-packages/customtkinter;customtkinter/"

MacOS
----------------------------------------------------------------

.. code-block:: bash

    N2390113:193-msa-grr jli8$ python3 -m venv venv
    N2390113:193-msa-grr jli8$ source venv/bin/activate
    (venv) N2390113:193-msa-grr jli8$ which python
    /Users/jli8/Library/CloudStorage/SynologyDrive-OnDemand/193-msa-grr/venv/bin/python
    (venv) N2390113:193-msa-grr jli8$ python --version
    Python 3.11.2


.. code-block:: text

    pip install --upgrade pip
    pip install tomlkit natsort python-dotenv
    pip install SQLAlchemy==1.4.46
    pip install mariadb
    pip install pandas matplotlib seaborn
    pip install pyarrow openpyxl customtkinter pypdf
    pip install GageRnR
    pip install pyinstaller
    pip freeze > requirements-macos.txt

    pyinstaller cli.py --noconfirm --windowed --name msag --distpath ~/Desktop/dist --icon=icon.icns --add-data=bundles/*:bundles/ --collect-all mariadb --collect-all sqlalchemy --collect-all pyarrow --collect-all customtkinter




Features:
================================================================

- This template uses a folder structure designed for ``pyinstaller``
- More details in detail here: `realpython-pyinstaller <https://realpython.com/pyinstaller-python/>`_

    .. code-block:: none

        reader/
        |
        ├── reader/
        |   ├── __init__.py
        |   ├── __main__.py
        |   ├── config.cfg
        |   ├── feed.py
        |   └── viewer.py
        |
        ├── cli.py
        ├── LICENSE
        ├── MANIFEST.in
        ├── README.md
        ├── setup.py
        └── tests


- This template is also designed for use with ``sphinx-doc``

    .. code-block:: none

        reader/
        |
        ├── reader/
        |   ├── ..
        |   └── ..
        |
        ├── docs/
        |   ├── /source/~
        |   └── build/~
        |
        ├── ..
        ├── README.md
        └── cli.py



TODO:
================================================================



Completed
----------------------------------------------------------------
- [DONE] dotenv compatibility with pyinstaller dist

    - remove dependency to dotenv, allow user to provide
      password via config.toml

- [DONE] bundles

    - msag/msag/bundles does not work on macos, because
      binary executable file msag is the same name as the dir msag
    - shift bundles out of msag, (or rely on pyinstaller --name
      msag_xx)



Others
================================================================

Documentations using Sphinx
----------------------------------------------------------------

Set up

.. code-block:: bash

    pip install -U sphinx
    pip install sphinx-rtd-theme

Basics

.. code-block:: bash

    mkdir docs
    cd docs
    sphinx-quickstart
    # separate source and build directories: y
    sphinx-build -b html source build/html



Autodoc

.. code-block:: bash

    # Enable autodoc in conf.py
    extensions = ['sphinx.ext.autodoc']

    cd ..
    # Make sure these folders exist (docs/, nibt/)
    sphinx-apidoc -o docs/source msag
    sphinx-build -b html docs/source docs/build/html


Change HTML theme

.. code-block:: bash

    pip install sphinx-rtd-theme

    # inside conf.py
    html_theme = 'sphinx_rtd_theme'



Readme file converter
----------------------------------------------------------------

Requires ``pandoc``

- https://stackoverflow.com/questions/45633709/how-to-convert-rst-files-to-md
- https://gist.github.com/zaiste/77a946bbba73f5c4d33f3106a494e6cd
- https://pandoc.org/
- ``brew install pandoc``


.. code-block:: bash

    #!/usr/bin/bash

    FILES=readme.rst

    while true; do
        read -p "Are you sure you want to proceed with overwriting readme.md? " yn
        case $yn in
            [Yy]* )
                for f in $FILES; do
                    filename="${f%.*}"
                    echo "Converting $f to $filename.md"
                    `pandoc $f -f rst -t markdown -o $filename.md`
                    echo "done"
                done
                break
                ;;

            [Nn]* )
                exit
                ;;

            * ) echo "Please enter Yes or No"
        esac
    done


