# RIGHT NOW THIS IS VIEW ONLY! It is for me only to work on, at least until I get to alpha. Everything here is temporary and *will* be changed. You will find a CD topic when I am ready. See you then :wave:

# frcVisionDataset

An *open* dataset allowing <abbr title="FIRST Robotics Competition">FRC</abbr> teams to upload match images, and download object detection datasets.

> [!WARNING]
> This project is in ***pre-alpha*** as of June 24, 2025. Everything is still at the "it works on my machine" point, except it doesn't even work for me! :sweat_smile:

![Static Badge](https://img.shields.io/badge/Licence-MIT-blue?style=for-the-badge)

## Todo:

See [issues](https://github.com/crummyh/frcVisionDataset/issues)

## Developing

If you are interested in helping, read this then see [issues](https://github.com/crummyh/frcVisionDataset/issues) for how you can help

Notes to self:
* To access the PostgreSQL database, run `sudo -u postgres psql`
* Try to use `git pull --rebase` instead of just pull

### Libraries Used

* Python 3
* FastAPI
* SQLModel
* SlowAPI
* Jinja
* Bootstrap
* AWS
  * S3
  * PostgreSQL

### Project Structure

```bash
📁 app/                          # Holds the main app
├── 📁 api/                      # The actual endpoints
│  ├─── 🐍 public_v1.py          # Publicly accessible API
│  ├─── 🐍 internal_v1.py        # Management and account API
│  └─── 🐍 web.py                # The website
├── 📁 core/                     # App-level core logic/config
│  ├─── 🐍 config.py             # Constants and configurable values
│  ├─── 🐍 dependencies.py       # Security dependencies
│  └─── 🐍 helpers.py            # Random common helper functions
├── 📁 db/                       # Database managers
│  └─── 🐍 database.py           # Manages the DB connection
├── 📁 models/                   # Data models
│  ├─── 🐍 models.py             # pydantic models for responses and requests
│  └─── 🐍 schemas.py            # SQLModel schemas representing tables
├── 📁 services/                 # Various services and abstractions
│  └─── 🐍 buckets.py            # AWS S3 bucket manager
├── 📁 tasks/                    # Asynchronous background tasks
│  ├─── 🐍 download_packaging.py # Packages images for batch downloading
│  └─── 🐍 image_processing.py   # Processes images for uploading
├── 📁 tests/                    # Tests
├── 📁 web/                      # Files that are for the website
│  ├── 📁 static/                # Static files
│  │  ├── 📁 css/                # CSS files
│  │  ├── 📁 images/             # Images
│  │  └── 📁 js/                 # JS files
│  └─── 📁 templates/            # Jinja HTML templates
└── 🐍 main.py                   # The main app entrypoint
```

### Running Locally
Linux:
```bash
# Pre-requirements
# * Have git installed
# * Have Python 3.10+ installed

# Setup
git clone "https://github.com/crummyh/frcVisionDataset.git" # (Or use ssh)
cd frcVisionDataset
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x setup.sh
./setup.sh
# Now start working!
# To run the app run:
fastapi dev app/main.py
# When you are done run:
deactivate
```

Windows:
Good luck, have fun!

Mac:
Probably similar to the Linux instructions, good luck!
