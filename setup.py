""" Build python package for pre-commit hooks"""
from pathlib import Path
from typing import Sequence

from setuptools import find_packages , setup

def read_requirements(filename: str) -> Sequence[str]:
    """Get requirements.txt as a list"""
    return open(Path(__file__).parent / filename, encoding="utf-8").read()

setup(
    name='common-pre-commit-hooks',
    packages=find_packages(exclude=(['test*', 'tmp*'])),
    version="1.0.0",
    description='Pre-commit hooks for code quality validation',
    url='hhttps://github.ibm.com/code-assistant/wca4z-agents-dev-scripts',
    keywords=['secret-management', 'pre-commit', 'security', 'entropy-checks'],
    readme = "README.md",
    python_requires=">=3.12",
    install_requires=read_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'commit_msg = pre_commit_hooks.commit_msg:main',
            'coverage_checks = pre_commit_hooks.coverage_checks:main',
            'pylint_checks = pre_commit_hooks.pylint_checks:main',
            'icr_checks = pre_commit_hooks.icr_image_checks:main'
        ],
    },
    classifiers=[
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.12",
        "License :: IBM",
        "Typing :: Typed",
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Utilities',
        'Environment :: Console',
        'Operating System :: OS Independent',
    ],
)
