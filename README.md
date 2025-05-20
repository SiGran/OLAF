
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

note: There's also a requirements.txt

### Pre-requisites
Find and follow instructions online for installing the following:
1. [Python](https://www.python.org/downloads/)
2. [Git](https://git-scm.com/downloads)
3. Optional: [Pycharm](https://www.jetbrains.com/pycharm/download/)

Please note that pycharm is not required to use this project. Feel free to use your favorite IDE or text editor.
To make installation as beginner-friendly as possible, we use pycharm to simplify the installation process. If you are
more familiar with installing software packages and setting up your environment, you should be able to find the parts
in these instructions to install it without pycharm.

### Installation
#### Install uv on windows
Install uv with pipx:
1. Open windows powershell and verify that python is installed on your computer.
```bash
py --version
```
<img width="1280" alt="IScompinstall1" src="https://github.com/user-attachments/assets/6c3f7fc1-6cd2-43a7-a68e-02d3e6f2c589" />

2.Then run the following command to install pipx for your user:
```bash
py -m pip install --user pipx"
```
3. Ensure that the pipx directory is added to PATH (more information on this [here](https://phoenixnap.com/kb/add-python-to-path)).
```bash
py -m pipx ensurepath
```
4. Close and re-open powershell for the PATH changes to take effect.
5. Install uv with pipx.
```bash
py -m pipx install uv
```
<img width="867" alt="IScompinstall3" src="https://github.com/user-attachments/assets/30655eb8-408c-4532-bd97-ed331f6a8c2d" />

6. Check which versions of python are available to install with uv
```bash
uv python list
```
7. Install python 3.11.12 (or whatever version of python 3.11.x is available)
```bash
uv python install 3.11.12
```

#### Install uv on MacOS & Linux
On most Unix based distro's like MacOS and Ubuntu Python should already be installed.
Adjust steps (2), (4), (5) to however you call python in the terminal.
E.g. 
```
pip install --user pipx
```
Steps (6) and (7) are the same for MacOS and PC.

##### Install the project
7. Open pycharm (must be version 2024.3.2 or later) and navigate to File --> Project from Version Control. OR if using pycharm for the first time, open the application and select "clone repository."
8. Copy/paste the github link below for the URL and choose a directory where you would like to store the project. You can insstall git at this stage if you have not already.
```bash
https://github.com/SiGran/OLAF.git
```
<img width="752" alt="IScompinstall7" src="https://github.com/user-attachments/assets/6e0871a4-940f-4dc8-90c2-ab57e82b2ec7" />

#### Activate the virtual environment
9. Open a powershell terminal in pycharm and run the following to create the virtual environment:
```bash
uv venv
```
<img width="1041" alt="IScompinstall8" src="https://github.com/user-attachments/assets/c122ca24-eb8d-4739-95fd-908f44ab0ee6" />

10. Run the .venv\Scripts\activate command.

11. Run "uv sync" in the terminal.
```bash
uv sync
```
12. Close and re-open pycharm.

#### Select the interpreter
14. Select the interpreter at the bottom right hand corner of the application and nagivate to "add local interpreter."
15. Select "select existing" and "uv" for the type of interpreter. If pycharm did not automatically detect where uv is installed on your computer, find its location and use this for "path to uv." Set the virtual environment (uv env use) by navigating to the "python.exe" installed in the "Scripts" folder where you installed the program.

<img width="1037" alt="IScompinstall10" src="https://github.com/user-attachments/assets/9b54f8a3-5ccf-437b-9a49-d8cbab0a5935" />
