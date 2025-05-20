# COVAS:NEXT {{cookiecutter.project_name}}

{{cookiecutter.description}}


## Features

- Feature 1
- Feature 2


## Installation

Unpack the plugin into the `plugins` folder in COVAS:NEXT, leading to the following folder structure:
* `plugins`
    * `{{cookiecutter.project_slug}}`
        * `{{cookiecutter.project_slug}}.py`
        * `requirements.txt`
        * `deps`
    * `OtherPlugin`

# Development
During development, clone the COVAS:NEXT repository and place your plugin-project in the plugins folder.  
Install the dependencies to your local .venv virtual environment using `pip`, by running this command in the `{{cookiecutter.project_slug}}` folder:
```bash
  pip install -r requirements.txt
```

# Packaging
Use the `./pack.ps1` script to package the plugin and any Python dependencies in the `deps` folder.
    
## Acknowledgements

 - [COVAS:NEXT](https://github.com/RatherRude/Elite-Dangerous-AI-Integration)
