from setuptools import setup, find_packages

setup(
    name='titan-scraper',
    version='2.0.0',
    description='Next-gen Anti-Detection Scraper with AI & Browser Fallback',
    author='Titan Team',
    packages=find_packages(),
    install_requires=[
        'requests>=2.28.0',
        'playwright>=1.40.0',
        'fake-useragent>=1.4.0',
        'SpeechRecognition>=3.10.0',
        'pydub>=0.25.1',
        'torch>=2.0.0',
        'torchvision>=0.15.0',
        'pillow>=10.0.0',
        'numpy>=1.24.0'
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'titan-train=train_captcha:main',
        ],
    },
)
