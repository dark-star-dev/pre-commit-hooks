""" Module to generate .pre-commit-config.yaml for a repository"""
from typing import TypedDict, NotRequired
from pathlib import Path
import yaml
import requests
from pre_commit_hooks.precommit import PreCommitPythonBase

class ConfigEntry(TypedDict):
    """pre-commit config entry"""
    name :NotRequired[str]
    id : str
    entry:NotRequired[str]
    language: NotRequired[str]
    always_run: NotRequired[bool]
    verbose: NotRequired[bool]
    pass_filenames: NotRequired[bool]
    require_serial: NotRequired[bool]
    description: NotRequired[str]
    log_file: NotRequired[str]
    minimum_pre_commit_version: NotRequired[str]
    args: NotRequired[list[str]]
    stages: NotRequired[list[str]]

class RepoEntry(TypedDict):
    """pre-commit repository entry"""
    repo:str
    rev:str
    hooks:list[ConfigEntry]

class ConfigData(TypedDict):
    """pre-commit-config base structure"""
    repos: list[RepoEntry]

class ConfigGenerator(PreCommitPythonBase):
    """Generator for pre-commit-config.yaml configuration"""

    _filename:str ="/.pre-commit-config.yaml"
    filepath:Path
    config_data: ConfigData

    def __init__(self, directory:str) -> None:
        self.filepath = Path(directory+self._filename)
        if self.filepath.exists():
            with open(file=self.filepath, mode="r", encoding="utf-8") as config_file:
                self.config_data = yaml.safe_load(config_file)
        else:
            self.config_data =  {"repos": []}

    def write_config(self) -> bool:
        """Generate .pre-commit-config.yaml from a list of RepoEntry objects"""
        with open(file=self.filepath, mode="w", encoding="utf-8") as config_file:
            yaml.safe_dump(
                self.config_data,
                config_file,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )
        return True

    def add_config(self, configuration: RepoEntry) -> bool:
        """Add a single repo configuration to existing config_data"""
        # Add new configuration
        self.config_data["repos"].append(configuration)
        return True

    def _get_latest_tag(self,url:str)-> str|None:
        rev: str|None= None
        latest_request = requests.get(
            url=url,
            timeout=20
            )
        if latest_request.status_code == 200 :
            request_json: dict = latest_request.json()
            if "tag_name" in request_json.keys():
                rev = request_json["tag_name"]
        return rev

    def _get_latest_tag_or_default(self,url:str,default_tag :str) ->str:
        # find latest tag or use default_tag
        rev: str = default_tag
        result = self._get_latest_tag(url)
        return rev if result is None else result

    def add_detect_secrets_config(self) -> bool:
        """ Add Detect secrets configuration to config_data"""
        detect_secrets_rev: str = self._get_latest_tag_or_default(
            url="https://api.github.com/repos/IBM/detect-secrets/releases/latest",
            default_tag="0.13.1+ibm.64.dss"
            )

        detect_secrets_config = ConfigEntry(
            id="detect-secrets",
            args=["--baseline", ".secrets.baseline", "--use-all-plugins"],
            stages= ["pre-commit"]
            )
        detect_secrets_repo = RepoEntry(
            repo="https://github.com/ibm/detect-secrets",
            rev=detect_secrets_rev,
            hooks=[detect_secrets_config]
            )
        self.config_data["repos"].append(detect_secrets_repo)
        return True
