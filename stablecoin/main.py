import os
import yaml
import logging
from datetime import datetime
import pyinsightic
from yaml.scanner import ScannerError
import log_config

# Configure logging at the start
log_config.setup_logging()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisRunner:
    def __init__(self, analysis_function, check_condition):
        self.analysis_function = analysis_function
        self.check_condition = check_condition

    def __call__(self, project_dir, data):
        if not self.check_condition(data):
            logger.info(
                f"Required conditions not met for {self.analysis_function.__name__} in {project_dir}. Skipping analysis."
            )
            return
        logger.info(f"Running {self.analysis_function.__name__} for {project_dir}")
        timestamp = "20240305"
        # timestamp = datetime.now().strftime("%Y%m%d")
        file_name = f"{self.analysis_function.__name__}.json"
        analysis = self.analysis_function(project_dir=project_dir)
        analysis.run_analysis(timestamp, file_name=file_name)


# Condition check functions
def check_stablecoin(data):
    return any(
        item["title"] == "Technological Details"
        for item in data.get("security_and_compliance", [])
        if "Token launch"
        in (blockchain["title"] for blockchain in item.get("value", []))
    )


def check_linkedin(data):
    return "linkedin" in data.get("links", {}) and data["links"]["linkedin"] not in [
        None,
        "",
    ]


def check_twitter(data):
    return "twitter" in data.get("links", {}) and data["links"]["twitter"] not in [
        None,
        "",
    ]


def check_security_assessment(data):
    return bool(data.get("security_report"))


def check_smart_contract_validator(data):
    whitepaper_uri = data.get("whitepaper", "")
    code_uri = ""

    # Extracting code URI using the provided logic
    for item in data.get("security_and_compliance", []):
        if item["title"] == "Technological Details":
            for dic in item.get("value", []):
                if dic["title"] == "Smart Contract":
                    code_uri = dic["value"]
                    break
            if code_uri:  # Exit the loop early if code_uri is found
                break

    # Ensure both whitepaper and code URI exist and are not empty/None
    return bool(whitepaper_uri and code_uri)


def check_sosovalue(data):
    # will run for all projects
    return True


# AnalysisRunner instances for each analysis
analyses = [
    # AnalysisRunner(pyinsightic.Stablecoin, check_stablecoin),
    # AnalysisRunner(pyinsightic.Linkedin, check_linkedin),
    # AnalysisRunner(pyinsightic.Twitter, check_twitter),
    # AnalysisRunner(pyinsightic.SosoValue, check_sosovalue),
    AnalysisRunner(pyinsightic.SmartContractValidator, check_smart_contract_validator),
    # AnalysisRunner(pyinsightic.SecurityAssessment, check_security_assessment),
]


def main(test_folders=None):
    for dir in os.listdir("."):
        if test_folders and dir not in test_folders:
            continue
        dir_path = os.path.join(".", dir)
        if os.path.isdir(dir_path) and os.path.exists(
            os.path.join(dir_path, "data.yml")
        ):
            logger.info(f"Processing folder: {dir}")
            data_path = os.path.join(dir_path, "data.yml")
            try:
                with open(data_path, "r") as file:
                    content = file.read()
                    # make sure it is spaces instead of tab
                    fixed_content = content.replace("\t", "    ")
                    data = yaml.safe_load(fixed_content)
            except ScannerError:
                logger.error("Invalid yaml format")
                return
            for analysis in analyses:
                analysis(dir_path, data)


if __name__ == "__main__":
    main()
    # os.chdir("stablecoin") # change directory for local test
    # main(test_folders=["dai"])
