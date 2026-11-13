
# Setup Guide

## 1. Purpose

This document explains how to prepare and run the SmartStock AI development environment.

The primary development environment is:

- Linux.
- Zorin OS 18.1.
- Python 3.
- SQLite.
- Streamlit.

The guide prioritizes a lightweight setup suitable for a machine with limited CPU and integrated graphics.

The application does not require a dedicated GPU.

---

## 2. Prerequisites

Install or verify:

- Python 3.
- Python virtual environment support.
- pip.
- Git.
- A code editor.
- Terminal access.

Verify Python:

```bash
python3 --version
```

Verify pip:

```
python3 -m pip --version
```

Verify Git:

```
git --version
```

If virtual environment support is missing on a Debian-based distribution, install the corresponding package:

```
sudo apt update
sudo apt install python3-venv python3-pip
```

Use the Python version supported by the project's selected dependencies.

## 3. Get the Project

If the project already exists locally:

```
cd path/to/smartstock-ai
```

If it is hosted in a Git repository:

```
git clone <repository-url>
cd smartstock-ai
```

Replace the placeholder with the actual repository URL.

Do not invent or assume a repository URL.

## 4. Create a Virtual Environment

From the project root:

```
python3 -m venv .venv
```

Activate it:

```
source .venv/bin/activate
```

After activation, the terminal should indicate that the virtual environment is active.

To deactivate it:

```
deactivate
```

The virtual environment directory should not be committed to Git.

## 5. Install Dependencies

If `requirements.txt` exists:

```
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The dependency list should be based on the approved tech stack.

Expected libraries may include:

- streamlit
    
- pandas
    
- numpy
    
- scikit-learn
    
- joblib
    
- pytest
    

Do not install TensorFlow, PyTorch, or other heavy frameworks unless a documented requirement justifies them.

The exact versions should be maintained in the project's dependency file.

## 6. Environment Variables

The initial application may not require environment variables.

If configuration values are needed, use a local `.env` file only when the selected configuration approach supports it.

Example:

```
APP_ENV=development
```

This is illustrative.

Do not store secrets, passwords, API keys, or private credentials in source code.

Ensure local environment files are excluded from Git.

If the application does not require a `.env` file, do not create one unnecessarily.

## 7. Dataset Setup

The proposed historical dataset is:

Kaggle Store Item Demand Forecasting Competition

Source:

[https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data?utm_source=chatgpt.com)

The dataset should be downloaded manually from its official source unless an approved automated download workflow is introduced.

Recommended steps:

1. Open the dataset source.
    
2. Review its current download requirements.
    
3. Download the required files.
    
4. Extract the files.
    
5. Place them in the project's designated data directory.
    
6. Confirm the actual file names and columns.
    
7. Run the project's data validation process.
    

A possible local structure:

```
data/
├── raw/
├── processed/
└── external/
```

The final paths must match the project structure documentation.

### Important Dataset Rules

- Raw source data should remain unchanged.
    
- Processed data should be reproducible where possible.
    
- Large datasets should not be committed to Git by default.
    
- Dataset paths should be configurable where necessary.
    
- Do not assume the dataset is already available locally.
    
- Do not commit Kaggle credentials.
    

## 8. Database Setup

The application uses SQLite as its proposed operational database.

The database initialization process should be implemented in the project.

After that process is available, run the documented initialization command.

The exact command depends on the final project structure.

For example, if a database initialization script is implemented:

```
python -m <database_initialization_module>
```

Replace the placeholder with the actual module path.

Do not create a database manually with an undocumented schema.

### Database Location

The database file should be stored in the designated application data directory.

For example:

```
data/
└── smartstock.db
```

The final location must follow the project configuration.

Local database files should generally not be committed to Git.

## 9. Model Artifacts

The forecasting model may be saved using Joblib.

A possible structure:

```
artifacts/
└── models/
    ├── demand_model.joblib
    └── model_metadata.json
```

The final file names and paths must match the model configuration.

Important:

- Model artifacts should be generated through the training pipeline.
    
- Do not assume a trained model already exists.
    
- Do not use an incompatible or outdated model artifact.
    
- Keep model metadata consistent with the saved model.
    
- Avoid committing large artifacts unless explicitly required.
    

If no trained model exists, follow the documented training process before using ML inference.

## 10. Run the Application

Activate the virtual environment:

```
source .venv/bin/activate
```

Run Streamlit using the actual application entry point.

For example, if the entry point is `app.py` in the project root:

```
streamlit run app.py
```

If the approved project structure uses another entry point, replace `app.py` with the correct path.

Streamlit should display a local application URL in the terminal.

Open that URL in a browser.

## 11. Run Tests

With the virtual environment active:

Run the full test suite (the package lives under `src/`, so the path
must be on `PYTHONPATH`):

```
PYTHONPATH=src python -m pytest
```

Run one file or class while developing:

```
PYTHONPATH=src python -m pytest tests/test_services_analytics.py
```

Integration tests (real `app.py` startup and end-to-end workflows):

```
PYTHONPATH=src python -m pytest tests/integration
```

Note: the repository has no separate `tests/unit` layout — tests are
organized flat under `tests/` by layer (repositories, database, domain,
ML, services, pages, integration).

## 12. Recommended Development Workflow

For normal development:

1. Open the project directory.
    
2. Activate `.venv`.
    
3. Review the relevant task and documentation.
    
4. Implement one small task.
    
5. Run the relevant tests.
    
6. Fix discovered issues.
    
7. Run broader tests when appropriate.
    
8. Update task progress.
    
9. Commit changes when the work is stable.
    

Example:

```
source .venv/bin/activate

python -m pytest

streamlit run app.py
```

The application command should use the confirmed entry point.

## 13. Git Guidelines

Before committing:

```
git status
```

Review the changed files.

Avoid committing:

- `.venv/`
    
- `__pycache__/`
    
- `.pytest_cache/`
    
- Local SQLite database files.
    
- Raw datasets.
    
- Private environment files.
    
- Temporary files.
    
- Unnecessary generated artifacts.
    

Use meaningful commit messages.

Examples:

```
feat: add product management service
feat: implement sales recording
feat: add CSV validation
test: add inventory calculation tests
fix: prevent duplicate sales imports
docs: update forecasting strategy
```

Only use commit messages that accurately describe the actual changes.

## 14. Troubleshooting

### Python Command Not Found

Try:

```
python3 --version
```

Use `python3` to create the virtual environment if `python` is unavailable.

### Virtual Environment Creation Fails

Install the required system package:

```
sudo apt install python3-venv
```

Then retry:

```
python3 -m venv .venv
```

### Dependencies Fail to Install

Check:

- Python version compatibility.
    
- Active virtual environment.
    
- Internet connection.
    
- Dependency versions.
    
- Error output from pip.
    

Avoid randomly installing system packages to resolve Python dependency conflicts.

### Streamlit Command Not Found

Verify that the virtual environment is active:

```
source .venv/bin/activate
```

Then verify installation:

```
python -m pip show streamlit
```

If it is missing, install the project's dependencies again.

### Database Errors

Check:

- Database file path.
    
- Initialization process.
    
- SQLite permissions.
    
- Current schema.
    
- Connection handling.
    

Do not delete the database as a first troubleshooting step.

Deleting a database may permanently remove operational data.

### Model Loading Errors

Check:

- Whether the model artifact exists.
    
- Whether the correct path is configured.
    
- Whether the model was trained successfully.
    
- Whether the installed scikit-learn version is compatible.
    
- Whether the metadata matches the model.
    

Do not silently replace a failed model with random predictions.

### Application Runs Slowly

Check:

- Dataset size.
    
- Repeated data loading.
    
- Repeated model training.
    
- Expensive calculations inside Streamlit reruns.
    
- Unnecessary database queries.
    
- Chart rendering overhead.
    

Prefer loading and training models through dedicated workflows instead of retraining during every normal page interaction.

## 15. Performance Guidelines

The target development machine uses an integrated GPU and a relatively modest CPU.

Therefore:

- Prefer CPU-friendly ML models.
    
- Use scikit-learn for the initial forecasting implementation.
    
- Avoid unnecessary deep learning frameworks.
    
- Avoid loading the full dataset repeatedly.
    
- Cache expensive read-only operations where appropriate.
    
- Avoid training models during normal dashboard rendering.
    
- Use smaller datasets for automated tests.
    
- Profile actual bottlenecks before optimizing.
    

Do not introduce performance complexity without evidence of a real problem.

## 16. Setup Completion Checklist

- Python is installed.
    
- Git is available.
    
- Project repository is available.
    
- Virtual environment is created.
    
- Virtual environment is activated.
    
- Dependencies are installed.
    
- Dataset is available if required.
    
- Database initialization works when implemented.
    
- Model artifacts are available when required.
    
- Streamlit application starts.
    
- Automated tests can run.
    

## 17. Notes for AI Agents

Before changing setup instructions:

1. Inspect the actual project structure.
    
2. Verify the dependency file.
    
3. Verify the application entry point.
    
4. Verify the database initialization process.
    
5. Verify the dataset paths.
    
6. Verify the model artifact paths.
    

Do not leave example commands presented as working commands when the corresponding files or modules do not exist.

Update this document whenever the actual setup process changes.