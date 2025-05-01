
# OLAF
OpenSource Library for Automating Freezing data acquisition from Ice Nucleation Spectrometer (OLAF DaQ INS).
Documentation can be found [here](https://sigran.github.io/OLAF/).
## Getting Started
 This project's virtual environment and dependencies are managed by [uv](https://docs.astral.sh/uv/). 

### Background information
When working with many different Python projects, it is highly recommended to use a 1) virtual environment and 2) a package manager.
1) A virtual environment is a self-contained directory that contains a Python installation for a particular version of Python, plus a number of additional packages.
2) A package manager is a tool that automates the process of installing, upgrading, configuring, and removing packages inside a virtual environment.

There are multiple options to manage versions of python and packages, but this project uses one package and project manager, [uv](https://docs.astral.sh/uv/).

### Pre-requisites
Find and follow instructions online for installing the following:
1. [Python](https://www.python.org/downloads/)
2. [Git](https://git-scm.com/downloads)
3. Optional:[Pycharm](https://www.jetbrains.com/pycharm/download/)

Please note that pycharm is not required to use this project. Feel free to use your favorite IDE or text editor.
To make installation as beginner-friendly as possible, we use pycharm to simplify the installation process. If you are
more familiar with installing software packages and setting up your environment, you should be able to find the parts
in these instructions to install it without pycharm.

### Installation on windows
#### uv
Install uv with pipx:
1. Open windows powershell and verify that python is installed on your computer. <img width="1280" alt="IScompinstall1" src="https://github.com/user-attachments/assets/6c3f7fc1-6cd2-43a7-a68e-02d3e6f2c589" />
Then run the following command:
```bash
py -m pip install --user pipx"
```
2. Ensure that the pipx directory is added to PATH (more information on this [here](https://phoenixnap.com/kb/add-python-to-path)).
```bash
py -m pipx ensurepath
```
3. Close and re-open powershell for the PATH changes to take effect.
4. Install uv with pipx.
```bash
py -m pipx install uv
```
5. Check which versions of python are available to install with uv
```bash
uv python list
```
6. Install python 3.11.12 (or whatever version of python 3.11.x is available)
```bash
uv python install 3.11.12
```
##### Install the project
Install the project dependencies:
10. Navigate to the project directory where `pyproject.toml` is located. 
Note: skip this step when using pycharm; it should already be in this directory.
```bash
cd ~/path/to/olaf
```
Replace `~/path/to/` with the path to the project directory.
11. Run the following command to install the project dependencies:
```bash
poetry install
```
12. Run the following command to verify the installation:
```bash
poetry show
```
The output should list the project dependencies.

##### Activate the uv virtual environment
select interpreter in pycharm: 
bottom right, select interpreter --> existing interpreter --> select poetry.
<add images>








## Old instructions (update these to just be linux/mac instructions)
 1. [Install Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
    Use the following command in a terminal to install Poetry:
    For Linux, macOS
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```
    or Windows (Powershell)
    ```bash
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
    ```
 2. Set environment:
    1. Make sure you have a python version 3.11 or higher installed on your machine. If not, you can install it using pyenv.
       ```bash
       pyenv install 3.12.0
       ```
       `Replace 3.12.0 with the version you want to install.`
    2. If you don't have pyenv installed, and in windows, you can install it using the instructions [here](https://github.com/pyenv-win/pyenv-win?tab=readme-ov-file#installation)
    ``` bash
    Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
    ```
    if that doesn't work, you can try:
    ``` bash
    
    ```
    Note: (see links in [background information](### Background information)).
       note: more on pyenv [here](https://realpython.com/intro-to-pyenv/).


3. Install virtual environment using poetry:
    > Note: if you're using PyCharm, [these](https://www.jetbrains.com/help/pycharm/poetry.html) 
   > are good instructions to follow to use Pycharms build-in environment/intepreter handler
   1. Set local environment to use the python version you want to use in terminal.
       ```bash
       poetry env use 3.12.0
       ```
       if that doesn't work:
       ```bash
         pyenv local 3.12.0
       ```
       `Replace 3.12.0 with the version you want to use.`
   2. Navigate to the project directory where `pyproject.toml` is located. 
   in Unix:
      ```bash
      cd ~/path/to/olaf
      ```
      `Replace ~/path/to/ with the path to the project directory.`
   3. Run the following command in the terminal:
        ```bash
           poetry install
        ```
    
       
## Usage
main.py is the main script that runs the OLAF DaQ INS.
       
       
    

Note's from Carson using this:

for windows
pip install pyenv-win --target $home\\.pyenv

pip install pyenv-win --target %USERPROFILE%\\.pyenv --no-user --upgrade
pyenv install 3.12.0

All the path stuff with variable

pip install seems to be the best.

pip install poetry


NEED TO USE command prompt (not powershell)
pip install pyenv
pyenv install 3.11.0
pyenv gloabl 3.11.0
pip install poetry
poetry install

set intepreter in pycharm to the virtual environment created by poetry
pyproject.

