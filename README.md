# nft-metadata-api
Python API server for LeaseNFT Metadata

## Framework

This project is written using the [Google App Engine](https://cloud.google.com/appengine) IaaS (Infrastructure as a Service) framework.


## Installation and setup
* Clone this repository

  `git clone <repo>`

* cd into the cloned repo

  `cd nft-metadata-api`

* Install Python and dependencies

  * Python 3.7 is a pre-requisite, and can be installed from [here](https://www.python.org/downloads "Python version downloads")

  * Install `gcloud`

  * Install virtualenv from pip

    `pip install virtualenv` or `pip3 install virtualenv`
    *Note: Sudo privileges may be required.*

  * Create a virtual environment

    `virtualenv -p python3.7 --no-site-packages ~/nft-metadata-api-venv`

  * Activate the virtual environment

    `source ~/nft-metadata-api-venv/bin/activate`

  * Install dependencies from requirements.txt via pip

    `pip install -r requirements.txt`

## Development
* In the project folder, add an empty folder `images/output/`

* In the project folder, add project Storage credentials in the file `credenetials/google-storage-credential.json`

* In the project folder, add `secret.py` file, and add a settings dict with the PROJECT_ID and STORAGE_BUCKET

* Run the server on localhost

  `python main.py`
