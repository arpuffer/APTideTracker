# Tidetracker

# Set up environment

```
sudo apt-get install swig
```

### Create python virtual environment and install python dependencies
```
python -m venv .venv
source /.venv/bin/activate
pip install spidev matplotlib numpy gpiozero lgpio noaa_coops
```

### Add crontab entry to execute tide tracker script within the appropriate virtual environment

```
# Edit crontab
crontab -e

# Add the following
* * * * * /path/to/project/.venv/bin/python /path/to/project/tide_tracker.py
```