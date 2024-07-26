# OLAF
OpenSource Library for Automating Freezing data acquisition from Ice Nucleation Spectrometer (OLAF DaQ INS)


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
2) and for managing it: [Poetry](https://python-poetry.org/docs/).

If you're on windows and want some more information: [some background](https://endjin.com/blog/2023/03/how-to-setup-python-pyenv-poetry-on-windows)

### Installation steps
 1. [Install Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
    Use the following command in a terminal to install Poetry:
    For Linux, macOS, Windows (WSL)
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
    2. If you don't have pyenv installed, you can install it using the instructions [here]( 
    Note: (see links in [background information](### Background information)).
       note: more on pyenv [here](https://realpython.com/intro-to-pyenv/).

3. Install virtual environment using poetry:
    > Note: if you're using PyCharm, [this](https://www.jetbrains.com/help/pycharm/poetry.html) 
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
       
       
    