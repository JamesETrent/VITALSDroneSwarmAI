
## Setup
### Download AI Models
1. Download [Ollama](https://ollama.com/download)

2. Browse available models [here](https://ollama.com/library)

3. Find model name as shown below:
![Logo](https://i.ibb.co/KFT7xtJ/model-id.png)

4. Dowload the model locally.
`ollama pull [MODEL_NAME]`
### Setup Python Virtual Environment
With a terminal open in repository,

if on mac/linux use:
`python3 -m venv llmtesting`

if on windows use:
`python -m venv llmtesting`
### Activate Virtual Environment
if on mac/linux use:
`source llmtesting/bin/activate`

Windows PowerShell(recomended):
`.\llmtesting\Scripts\activate.ps1`

Windows CMD:
`.\llmtesting\Scripts\activate.bat`

CLI should now be prefixed with (llmtesting)

Virtual environment can be deactivated with `deactivate`
### Install Dependencies
`pip install ollama inquirer` 

### Running Test Script
Set your name in config.cfg

Load any images you want to test into ./images directory

Run program using `python  main.py`

All downloaded models will be available for selection

When asked for prompt press "Enter" and a temporary text file will open. Write prompt save and exit.

Select one or several models which will run the given prompt

After a model runs it will ask you to score its response 1-10

Outputs will be saved to ./output directory
