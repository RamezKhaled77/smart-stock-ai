# Deployment Guide

## 1. Purpose

This document describes how to prepare, configure, and deploy the SmartStock AI application to a hosting environment.

It covers:

- Deployment prerequisites.
- Production environment requirements.
- Dependency management.
- Environment configuration.
- Database and file storage considerations.
- Machine learning model deployment.
- Security requirements.
- Deployment verification.
- Maintenance and troubleshooting.

The purpose is to provide a deployment strategy without introducing unnecessary platform-specific decisions before a hosting provider is selected.

---

## 2. Deployment Status

**Current Status: Not Deployed**

The application is currently planned as a local development project.

No production hosting provider has been formally selected.

The following decisions remain open:

- Hosting provider.
- Production operating environment.
- Database hosting strategy.
- Persistent file storage strategy.
- Model artifact storage strategy.
- Public access and authentication requirements.
- Domain and HTTPS configuration.
- Backup strategy.

The deployment process described here is a general preparation guide.

Actual deployment must wait until the hosting environment and required configuration are approved.

---

## 3. Deployment Architecture

### 3.1 Application Components

The application is expected to contain the following components:

| Component | Responsibility |
|---|---|
| Streamlit | Web application interface |
| Python | Application runtime |
| Pandas / NumPy | Data processing |
| Scikit-learn | Machine learning functionality |
| Plotly | Data visualization |
| SQLite | Initial application database |
| Joblib | Model serialization |
| CSV files | Data import and export |

The actual dependencies must be confirmed against the project's dependency configuration.

### 3.2 General Architecture

The expected deployment structure is:

```text
User Browser
     |
     v
Streamlit Application
     |
     v
Application Services
     |
     +------------------+
     |                  |
     v                  v
SQLite Database    ML Prediction Pipeline
     |                  |
     v                  v
Operational Data    Model Artifact
```

This is a logical deployment overview, not a finalized infrastructure architecture.

### 3.3 Deployment Considerations

The deployment environment must support:

- The selected Python version.
    
- Required Python dependencies.
    
- Streamlit execution.
    
- Database access.
    
- Required file permissions.
    
- Model artifact loading.
    
- Persistent storage when application data must survive restarts.
    

The selected hosting provider must be evaluated against these requirements.

## 4. Deployment Prerequisites

Before deployment, the following conditions should be satisfied.

### 4.1 Application Readiness

- Core application functionality is implemented.
    
- Required acceptance criteria are satisfied.
    
- Relevant tests have passed.
    
- Application starts successfully in a clean environment.
    
- Database initialization works.
    
- Required data files are available.
    
- Model loading works when forecasting functionality is enabled.
    
- Application errors are handled appropriately.
    
- No development-only configuration is required for production operation.
    

### 4.2 Repository Readiness

- Dependencies are documented.
    
- A supported Python version is specified.
    
- Required environment variables are documented.
    
- `.gitignore` excludes sensitive and generated files where appropriate.
    
- No credentials are stored in source code.
    
- The application entry point is documented.
    
- Deployment configuration is reviewed.
    

### 4.3 Deployment Approval

Before publishing the application:

- The hosting provider must be selected.
    
- The deployment configuration must be reviewed.
    
- Data storage requirements must be understood.
    
- Any expected hosting costs must be disclosed.
    
- The user must explicitly approve the deployment.
    

Preparing deployment files does not authorize publishing the application.

## 5. Python Environment

### 5.1 Python Version

The production environment must use a Python version compatible with the project's dependencies.

The exact supported version must be established and documented in the project setup configuration.

Do not assume that the production Python version is identical to the development machine's version.

### 5.2 Dependency Management

All direct application dependencies must be declared in the project's dependency configuration.

The deployment environment should install dependencies from the approved dependency file.

Example:

```
python -m pip install -r requirements.txt
```

The actual dependency file name must be confirmed from the repository.

Avoid installing arbitrary packages manually in production without updating the project's dependency configuration.

### 5.3 Clean Environment Verification

Before deployment, verify that the application works in a clean virtual environment.

Example:

```
python -m venv .venv

source .venv/bin/activate

python -m pip install --upgrade pip

python -m pip install -r requirements.txt
```

Then run the application's documented entry point.

This helps identify undeclared dependencies and environment-specific problems.

## 6. Application Configuration

### 6.1 Configuration Principles

Production configuration should be separated from application source code.

The application should not depend on hardcoded local machine paths or development-only settings.

Configuration should support:

- Database location.
    
- Dataset location.
    
- Model artifact location.
    
- Application-specific settings.
    
- External credentials, if introduced later.
    

### 6.2 Environment Variables

Environment variables may be used for configuration that differs between environments.

Potential configuration variables include:

|Variable|Purpose|Status|
|---|---|---|
|`APP_ENV`|Application environment|Proposed|
|`DATABASE_PATH`|SQLite database location|Proposed|
|`DATASET_PATH`|Dataset location|Proposed|
|`MODEL_PATH`|Trained model artifact location|Proposed|

These names are examples, not confirmed application configuration.

The final variable names and defaults must match the implemented configuration system.

### 6.3 Secrets

If external services or credentials are introduced:

- Store secrets in the hosting provider's secret-management system.
    
- Do not commit `.env` files containing real credentials.
    
- Do not expose secrets in application logs.
    
- Do not display credentials in the UI.
    
- Provide example configuration using placeholder values only.
    

The current project should not introduce secrets unnecessarily.

## 7. Database Deployment

### 7.1 Initial Database Strategy

SQLite is the proposed initial database for SmartStock AI.

It is suitable for a lightweight application with relatively simple operational requirements.

However, production deployment requires additional consideration.

### 7.2 Persistent Storage

SQLite stores application data in a database file.

The hosting environment must provide persistent storage if the application needs to preserve data across:

- Application restarts.
    
- Container restarts.
    
- Redeployments.
    
- Hosting instance replacements.
    

A temporary filesystem must not be treated as permanent database storage.

The exact persistent storage mechanism depends on the selected hosting provider.

### 7.3 Database Initialization

The application must have a reliable database initialization process.

Deployment should ensure that:

1. The configured database location is available.
    
2. Required directories exist.
    
3. Database tables are initialized safely.
    
4. Existing application data is preserved.
    
5. Initialization does not unintentionally overwrite an existing database.
    

Database initialization must be idempotent where practical.

It should be safe to run more than once without destroying existing data.

### 7.4 Database Backups

A production database should be backed up regularly.

The backup strategy should consider:

- Backup frequency.
    
- Backup retention.
    
- Backup location.
    
- Restore procedure.
    
- Database consistency.
    
- Access permissions.
    

The exact backup schedule remains an open deployment decision.

A backup process must not be considered reliable until restoration has been tested.

### 7.5 SQLite Limitations

SQLite may become unsuitable if the application requires:

- Multiple concurrent writers.
    
- Higher write throughput.
    
- Multiple application instances sharing the same database.
    
- More advanced database administration.
    
- Remote database access.
    

If these requirements emerge, evaluate a server-based database such as PostgreSQL.

A database migration must be planned and approved before implementation.

## 8. Dataset and File Storage

### 8.1 Dataset Handling

The project may use an external demand forecasting dataset for training and evaluation.

The dataset should not automatically be included in the deployment package.

Consider:

- Dataset size.
    
- Licensing and usage conditions.
    
- Whether the dataset is needed at runtime.
    
- Whether training is performed during deployment.
    
- Whether only the trained model is required for inference.
    

The production application should not load the full training dataset unnecessarily.

### 8.2 Operational Files

The application may generate or use:

- CSV import files.
    
- CSV export files.
    
- SQLite database files.
    
- Trained model artifacts.
    
- Model metadata.
    
- Temporary processing files.
    

Each file type should have an explicit storage policy.

### 8.3 File Persistence

Files that must survive application restarts should be stored in persistent storage.

Temporary files should be stored in an appropriate temporary location and cleaned up safely.

The application must not assume that its source directory is writable in every hosting environment.

## 9. Machine Learning Model Deployment

### 9.1 Model Artifact

The forecasting pipeline is expected to save a trained model artifact using Joblib.

The production application should load the trained model for inference rather than retraining it on every application startup.

### 9.2 Model Requirements

Before deployment, verify:

- The model artifact exists.
    
- The artifact is readable.
    
- The model was trained using the expected feature structure.
    
- Prediction input matches the training schema.
    
- Required metadata is available.
    
- Model loading errors are handled.
    
- The model is compatible with the deployed dependency versions.
    

### 9.3 Model Version Compatibility

Serialized models may depend on specific library versions.

The production environment should use compatible versions of:

- Python.
    
- Scikit-learn.
    
- NumPy.
    
- Pandas.
    
- Joblib.
    

A model should be retrained or validated when incompatible dependency changes occur.

Do not assume that an old model artifact will remain compatible with every future environment.

### 9.4 Training and Inference Separation

Training and inference should remain separate operations.

Recommended deployment behavior:

1. Train the model during the development or approved training process.
    
2. Evaluate the model.
    
3. Save the approved artifact and metadata.
    
4. Make the artifact available to the application.
    
5. Load the artifact when forecasting functionality is required.
    
6. Generate predictions using the approved inference pipeline.
    

Production startup should not automatically trigger expensive model training unless explicitly designed and approved.

### 9.5 Model Storage

The final model storage location is not yet defined.

The chosen approach must consider:

- Persistent storage.
    
- Artifact size.
    
- Version management.
    
- Access permissions.
    
- Backup requirements.
    

## 10. Streamlit Deployment

### 10.1 Application Entry Point

The final Streamlit entry point must be confirmed from the implemented project structure.

A typical command may look like:

```
streamlit run app.py
```

This is an example only.

Use the actual entry point defined by the repository.

### 10.2 Network Configuration

The application must listen on the network interface and port required by the hosting environment.

A typical hosting environment may provide a required port through an environment variable.

The exact configuration must follow the selected hosting provider's documentation.

Do not hardcode a provider-specific port unless the deployment environment requires it.

### 10.3 Streamlit Configuration

Streamlit configuration may be needed for:

- Server address.
    
- Port.
    
- Headless execution.
    
- File upload limits.
    
- Browser behavior.
    
- Logging.
    
- Theme.
    

Only settings that are actually required should be configured.

Avoid adding unnecessary configuration options.

### 10.4 Session and State Considerations

Streamlit applications may rerun scripts in response to user interactions.

Production behavior should be tested for:

- Database connection handling.
    
- Session state.
    
- Repeated form submissions.
    
- File uploads.
    
- Long-running operations.
    
- Concurrent user interactions.
    

Important application data must not exist only in temporary session state.

## 11. Security Considerations

Security requirements must be evaluated before public deployment.

### 11.1 Input Validation

All user-provided input must be validated.

This includes:

- Product information.
    
- Sales records.
    
- Inventory adjustments.
    
- CSV uploads.
    
- Date filters.
    
- Forecasting parameters.
    

Validation must happen at appropriate application boundaries, not only through UI widgets.

### 11.2 Database Safety

- Use parameterized SQL queries.
    
- Validate database operations.
    
- Avoid exposing raw database errors to users.
    
- Restrict database file access.
    
- Avoid destructive initialization behavior.
    

### 11.3 File Upload Safety

CSV uploads should be validated before processing.

Consider:

- File extension.
    
- File size.
    
- Required columns.
    
- Data types.
    
- Invalid values.
    
- Unexpected rows.
    
- Duplicate records.
    
- Malformed files.
    

Do not trust file extensions alone.

### 11.4 Authentication and Access Control

Authentication requirements have not yet been finalized.

Before public deployment, determine whether the application needs:

- User authentication.
    
- User roles.
    
- Access restrictions.
    
- Store-level data isolation.
    
- Administrative access.
    

A public deployment must not expose operational data simply because authentication has not been implemented.

### 11.5 HTTPS

Public production access should use HTTPS.

The hosting provider or approved infrastructure should handle TLS configuration.

### 11.6 Error Handling and Logging

Production logs should help diagnose failures without exposing:

- Credentials.
    
- Sensitive user data.
    
- Full private CSV contents.
    
- Unnecessary database records.
    

Detailed internal errors should not be displayed directly to end users.

## 12. Performance and Resource Considerations

The deployment environment should be evaluated against the application's expected resource usage.

Important considerations include:

- Python process memory.
    
- Streamlit application startup time.
    
- Database size.
    
- Dataset processing time.
    
- Model loading time.
    
- Forecast generation time.
    
- Concurrent users.
    
- File upload size.
    

The initial project is designed to use relatively lightweight Python ML libraries.

A GPU is not currently required by the proposed forecasting approach.

However, actual resource requirements should be measured after implementation and testing.

Avoid selecting a hosting plan based only on assumptions.

## 13. Deployment Procedure

The following is a general deployment checklist.

The exact commands and settings depend on the selected hosting provider.

### Step 1: Prepare the Application

- Confirm the application entry point.
    
- Confirm the dependency configuration.
    
- Verify that the application runs locally.
    
- Run relevant tests.
    
- Check application configuration.
    
- Remove development-only assumptions.
    

### Step 2: Prepare Deployment Configuration

- Select the hosting provider.
    
- Confirm Python version compatibility.
    
- Configure the application start command.
    
- Configure required environment variables.
    
- Configure persistent storage.
    
- Configure database initialization.
    
- Configure model artifact access.
    

### Step 3: Prepare Data

- Confirm the required operational database.
    
- Confirm whether initial sample data is needed.
    
- Confirm model artifact availability.
    
- Verify file permissions.
    
- Ensure private datasets are not published accidentally.
    

### Step 4: Deploy

Deployment should be performed only after explicit approval.

Follow the selected provider's official deployment instructions.

### Step 5: Verify the Deployment

After deployment, verify:

- The application starts successfully.
    
- The application is accessible through the intended URL.
    
- Required pages load.
    
- Database access works.
    
- Product operations work.
    
- Sales operations work.
    
- CSV import works.
    
- Forecasting works when enabled.
    
- Restocking recommendations work when enabled.
    
- Errors are handled correctly.
    
- Data persists after a restart when persistence is expected.
    

### Step 6: Record Deployment Information

Document:

- Hosting provider.
    
- Deployment environment.
    
- Application URL, if public.
    
- Deployment configuration.
    
- Database strategy.
    
- Persistent storage strategy.
    
- Model artifact strategy.
    
- Known deployment limitations.
    
- Date of deployment.
    

Never include credentials or secret values in documentation.

## 14. Post-Deployment Maintenance

After deployment, the application may require:

- Dependency updates.
    
- Security updates.
    
- Database backups.
    
- Database maintenance.
    
- Model retraining.
    
- Model evaluation.
    
- Error monitoring.
    
- Performance monitoring.
    
- Data cleanup.
    
- Bug fixes.
    

Maintenance should be performed carefully to avoid data loss or unexpected downtime.

Changes to production data or infrastructure must follow the applicable approval and backup requirements.

## 15. Troubleshooting

### 15.1 Application Fails to Start

Possible causes:

- Incorrect entry point.
    
- Missing dependencies.
    
- Unsupported Python version.
    
- Invalid configuration.
    
- Missing files.
    
- Incorrect file permissions.
    

Recommended checks:

1. Inspect deployment logs.
    
2. Confirm the Python version.
    
3. Confirm installed dependencies.
    
4. Verify the start command.
    
5. Check required configuration values.
    

### 15.2 Database Errors

Possible causes:

- Incorrect database path.
    
- Missing parent directory.
    
- Missing write permissions.
    
- Database initialization failure.
    
- Temporary storage being used unexpectedly.
    

Recommended checks:

1. Verify the configured database path.
    
2. Verify directory permissions.
    
3. Check database initialization.
    
4. Confirm persistent storage configuration.
    
5. Inspect database errors without exposing private data.
    

Do not delete or recreate an existing database as a troubleshooting shortcut.

### 15.3 Model Loading Errors

Possible causes:

- Missing model artifact.
    
- Incorrect model path.
    
- Incompatible library versions.
    
- Corrupted artifact.
    
- Incorrect file permissions.
    

Recommended checks:

1. Verify the artifact location.
    
2. Verify file existence and permissions.
    
3. Check dependency compatibility.
    
4. Validate the artifact in a controlled environment.
    
5. Retrain only when necessary and approved.
    

### 15.4 Data Does Not Persist

Possible causes:

- Temporary filesystem.
    
- Incorrect storage mount.
    
- Incorrect database path.
    
- Files being written to an ephemeral directory.
    

Recommended checks:

1. Identify where the application writes data.
    
2. Check whether that location is persistent.
    
3. Verify the hosting provider's storage behavior.
    
4. Test persistence after restart.
    
5. Restore from backup if data recovery is required.
    

## 16. Open Deployment Decisions

The following decisions must be resolved before final production deployment.

|ID|Decision|Status|
|---|---|---|
|DEP-001|Select hosting provider|Open|
|DEP-002|Confirm production Python version|Open|
|DEP-003|Confirm application entry point|Open|
|DEP-004|Select persistent storage strategy|Open|
|DEP-005|Confirm production database strategy|Open|
|DEP-006|Define backup and restore strategy|Open|
|DEP-007|Define model artifact storage|Open|
|DEP-008|Define authentication requirements|Open|
|DEP-009|Define public access policy|Open|
|DEP-010|Confirm deployment environment variables|Open|
|DEP-011|Define monitoring and logging strategy|Open|
|DEP-012|Define production update procedure|Open|

These decisions should be recorded in the project's decision log when formally resolved.

## 17. Deployment Completion Criteria

Deployment is considered successful only when:

- The approved hosting environment is configured.
    
- The application starts successfully.
    
- Required dependencies are installed.
    
- Required configuration is available.
    
- Database access works.
    
- Persistent storage works where required.
    
- Model loading works when forecasting is enabled.
    
- Required application workflows are accessible.
    
- Relevant deployment checks pass.
    
- Security requirements are addressed.
    
- Backup and recovery expectations are documented.
    
- Deployment information is recorded.
    
- Known limitations are documented.
    

Deployment preparation alone does not satisfy these criteria.

## 18. Current Deployment Policy

Until a hosting provider and production requirements are formally selected:

- Local development remains the primary environment.
    
- Deployment instructions remain platform-independent.
    
- SQLite remains the proposed initial database.
    
- No public production environment is assumed.
    
- No automatic deployment is authorized.
    
- No production data migration is authorized.
    
- No external paid service is assumed.
    
- No production credentials should be committed to the repository.
    

Any major change to these assumptions must be reviewed and documented.

## 19. Core Principle

Deployment must preserve the correctness, availability, and security of SmartStock AI.

A successful deployment is not simply an application that opens in a browser.

It must also preserve operational data, load the required model artifacts, handle errors safely, and behave consistently with the verified application implementation.