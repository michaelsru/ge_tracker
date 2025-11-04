from setuptools import setup

APP = ['getracker.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['rumps', 'requests', 'certifi'],
    'plist': {
        'LSUIElement': True,  # This makes it menu-bar only (no dock icon)
        'CFBundleName': 'OSRS GE Prices',
        'CFBundleDisplayName': 'OSRS GE Prices',
        'CFBundleIdentifier': 'com.osrs.geprices',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
