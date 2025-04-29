
# OLAF
OpenSource Library for Automating Freezing data acquisition from Ice Nucleation Spectrometer (OLAF DaQ INS).
Documentation can be found [here](https://sigran.github.io/OLAF/).
## Getting Started
 This projects (packages versions) dependencies are managed by [Poetry](https://python-poetry.org/docs/). 
 It's recommended to create a virtual environment (in order to maintain a usable system Python), 
 and use Poetry to install the dependencies.

### Background information
When working with a lot of different projects, and needing Python for your operating system, 
it's highly recommended to use a 1) virtual environment and 2) a package manager.
1) A virtual environment is a self-contained directory that contains a Python installation for a particular version of Python, plus a number of additional packages.
2) A package manager is a tool that automates the process of installing, upgrading, configuring, and removing packages inside a virtual environment.

There are multiple options to manage multiple versions of python and packages, but this project uses instructions for following popular options::
1) In order to manage multiple versions of python, you can use [pyenv](https://realpython.com/intro-to-pyenv/).
2) For package managed we use: [Poetry](https://python-poetry.org/docs/).

If you're on windows and want some more information: [some background](https://endjin.com/blog/2023/03/how-to-setup-python-pyenv-poetry-on-windows)

### Installation on windows
Some pre-requisites are needed to install the project on windows. 
Using Powershell inside pycharm:
1. Install pyenv-win 
2. Close pycharm and redo 
3. Install new environment: `pyenv install 3.11.0`
4. pip install poetry 
5. poetry install 
6. select interpreter in pycharm (bottom right, select interpreter --> existing interpreter --> select poetry)

#### Pre-requisites
Find and follow instructions online for installing the following:
1. [Python](https://www.python.org/downloads/)
2. [Git](https://git-scm.com/downloads)
3. Optional:[Pycharm](https://www.jetbrains.com/pycharm/download/)

Please note that pycharm is not required to use this project. Feel free to use your favorite IDE or text editor.
To make installation as beginner-friendly as possible, we use pycharm to simplify the installation process. If you are
more familiar with installing software packages and setting up your environment, you should be able to find the parts
in these instructions to install it without pycharm.

#### Installation steps
##### Pyenv
Install pyenv-win:
1. Open a powershell terminal in pycharm <add image>.
2. Run the following command:
```bash
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```
3. Close the terminal and open a new one.
4. Run the following command to verify the installation:
```bash
pyenv --version
```
The output should say `pyenv-win` and a version number.

##### Setting up the virtual environment
Install virtual environment and set it locally.
5. Run the following command to install python 3.11.0:
```bash
pyenv install 3.11.0
```
Note: if you get an error like `command not found`: restart pycharm and try again.
    If it still doesn't work, you need to add the path to python and/or pyenv to your [system environment variables](https://phoenixnap.com/kb/add-python-to-path).
6. Set the local python version to newly installed 3.11.0:
```bash
pyenv local 3.11.0
```
7. Run the following command to verify the python version:
```bash
python --version
```
The output should be `Python 3.11.0`.

##### Poetry
Install poetry:
8. Run the following command to install poetry:
```bash
pip install poetry
```
9. Run the following command to verify the installation:
```bash
poetry --version
```
The output should be a version number.

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

##### Activate the Poetry virtual environment
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

