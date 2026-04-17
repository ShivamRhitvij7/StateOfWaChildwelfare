import json
import os
import glob
import pytest

PARAM_DIR = "arm-template-parameters"
ADF_DIR = "adf"

ENVIRONMENTS = ["dev", "uat", "prod"]

REQUIRED_PARAMS = [
    "factoryName",
    "globalParameters_environment_value",
    "globalParameters_keyVaultBaseUrl_value",
    "globalParameters_storageAccountName_value",
    "globalParameters_sqlServerName_value",
    "globalParameters_sqlDatabaseName_value",
    "globalParameters_alertEmailRecipients_value",
]


def load_param_file(env):
    """Load and parse an environment parameter file."""
    path = os.path.join(PARAM_DIR, f"{env}.parameters.json")
    with open(path, "r") as f:
        return json.load(f)


class TestParameterFiles:
    """Validate that all environment parameter files are well-formed."""

    @pytest.mark.parametrize("env", ENVIRONMENTS)
    def test_param_file_exists(self, env):
        """Each environment must have a parameter file."""
        path = os.path.join(PARAM_DIR, f"{env}.parameters.json")
        assert os.path.exists(path), f"Missing parameter file for {env}"

    @pytest.mark.parametrize("env", ENVIRONMENTS)
    def test_all_required_params_present(self, env):
        """Each file must contain every required parameter."""
        data = load_param_file(env)
        params = data.get("parameters", {})
        for param in REQUIRED_PARAMS:
            assert param in params, (
                f"Missing '{param}' in {env}.parameters.json"
            )

    @pytest.mark.parametrize("env", ENVIRONMENTS)
    def test_no_empty_values(self, env):
        """No parameter should have an empty string value."""
        data = load_param_file(env)
        params = data.get("parameters", {})
        for key, val in params.items():
            assert val.get("value", "") != "", (
                f"Empty value for '{key}' in {env}.parameters.json"
            )

    @pytest.mark.parametrize("env", ENVIRONMENTS)
    def test_environment_value_matches_filename(self, env):
        """The environment global parameter must match the file it's in."""
        data = load_param_file(env)
        env_value = data["parameters"]["globalParameters_environment_value"]["value"]
        assert env_value == env, (
            f"Environment mismatch: file is {env} but parameter says '{env_value}'"
        )

    def test_no_cross_environment_contamination(self):
        """Dev values should never appear in UAT or Prod files."""
        dev_data = load_param_file("dev")
        dev_kv = dev_data["parameters"]["globalParameters_keyVaultBaseUrl_value"]["value"]

        for env in ["uat", "prod"]:
            other_data = load_param_file(env)
            other_kv = other_data["parameters"]["globalParameters_keyVaultBaseUrl_value"]["value"]
            assert other_kv != dev_kv, (
                f"{env} Key Vault URL is same as dev — likely a copy-paste error"
            )

    def test_param_keys_consistent_across_environments(self):
        """All environment files should define the exact same set of keys."""
        all_keys = {}
        for env in ENVIRONMENTS:
            data = load_param_file(env)
            all_keys[env] = set(data.get("parameters", {}).keys())

        reference = all_keys["dev"]
        for env in ["uat", "prod"]:
            missing = reference - all_keys[env]
            extra = all_keys[env] - reference
            assert not missing, f"{env} is missing params: {missing}"
            assert not extra, f"{env} has extra params: {extra}"


class TestNoHardcodedSecrets:
    """Scan ADF JSON files for accidentally hardcoded secrets."""

    # Patterns that should NEVER appear in ADF JSON
    FORBIDDEN_PATTERNS = [
        "DefaultEndpointsProtocol=https;AccountName=",  # Storage conn string
        "Server=tcp:",                                    # SQL conn string
        "Password=",                                      # Any password
        "SharedAccessSignature=",                         # SAS token
        "AccountKey=",                                    # Storage account key
    ]

    def _get_all_adf_json_files(self):
        """Recursively find all JSON files in the ADF directory."""
        return glob.glob(os.path.join(ADF_DIR, "**", "*.json"), recursive=True)

    @pytest.mark.parametrize("pattern", FORBIDDEN_PATTERNS)
    def test_no_secrets_in_adf_artifacts(self, pattern):
        """No ADF JSON file should contain hardcoded credential patterns."""
        for filepath in self._get_all_adf_json_files():
            with open(filepath, "r") as f:
                content = f.read()
            assert pattern not in content, (
                f"🚨 Potential hardcoded secret found in {filepath}: "
                f"contains '{pattern[:30]}...'"
            )