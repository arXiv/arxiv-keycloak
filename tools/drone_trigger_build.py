"""Trigger a build on a drone server and wait for it to finish."""

import argparse
import logging
import os
import time

import requests
from enum import Enum

DRONE_SERVER = os.environ.get('DRONE_SERVER', 'https://drone.arxiv.org')


def _setup_drone_token() -> str|None:
    do_local = False
    drone_token = None
    try:
        from google.cloud import secretmanager
        from google.api_core.exceptions import NotFound
    except (ImportError, ModuleNotFoundError) as e:
        do_local = True

    if not do_local:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = "projects/arxiv-development/secrets/drone_token/versions/latest"
            response = client.access_secret_version(name=name)
            drone_token = response.payload.data.decode('UTF-8')
        except (ImportError, ModuleNotFoundError, NotFound) as e:
            do_local = True

    if do_local:
        # If the secret manager is not available, use the environment variable
        # This is for local development only
        logging.warning("Google Cloud Secret Manager not available. Using environment variable.")
        if os.environ.get('DRONE_TOKEN'):
            drone_token = os.environ['DRONE_TOKEN']

    return drone_token

class DroneBuildStatus(str, Enum):
    """Drone build pipeline status."""

    success = "success"
    failure = "failure"
    timeout = "timeout"



class DroneBuild:
    """Class to trigger a build on a drone server and wait for it to finish."""

    def __init__(self, repo, namespace="arXiv", branch=None, commit=None) -> None:
        self.repo: str = repo
        self.namespace: str = namespace
        self.branch: str = branch
        self.commit: str = commit
        self.nr: int|None = None
        self.status: DroneBuildStatus|None = None

    def _send_request(self, component, method='GET', params=None):
        """Send a request to the Drone API.

        Args:
            component (str): The API sub-component (after /api/repos/NS/REPO/) to call.
            method (str): The HTTP method to use (GET, POST).
            params (dict): The parameters to send with the request.
        """
        url = f"{DRONE_SERVER}/api/repos/{self.namespace}/{self.repo}/{component}"
        logging.debug(f"Calling {url} with params {params}")
        headers = {
            'Authorization': f'Bearer {DRONE_TOKEN}',
            'Content-Type': 'application/json'
        }

        if method == 'GET':
            method = requests.get
        elif method == 'POST':
            method = requests.post
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        response = method(url, headers=headers, params=params)

        if response.status_code == 200:
            return response
        else:
            logging.error(f"Failed to call API: {response.status_code} - {response.text}")
            raise Exception("Failed to trigger build")


    def trigger(self) -> None:
        """Trigger a build for the specified repository and branch in Drone CI."""
        params = {}
        if self.branch:
            params['branch'] = self.branch
        if self.commit:
            params['commit'] = self.commit
        response = self._send_request('builds', method='POST', params=params)
        self.nr = response.json()['number']


    def current_status(self) -> bool:
        """Check if the build is currently running."""
        if self.nr is None:
            raise ValueError("Build number is not set. Trigger the build first.")
        response = self._send_request(f"builds/{self.nr}", method='GET')
        status = response.json()['status']
        logging.debug(f"Build status: {status}")
        return status


    def wait_until_finished(self, timeout=600) -> None:
        """Wait until the build is finished."""
        if self.nr is None:
            raise ValueError("Build number is not set. Trigger the build first.")

        budget = timeout
        while True:
            time.sleep(10)
            budget -= 10
            if budget <= 0:
                # TODO should we try to stop the build?
                logging.error("Timeout waiting for build to finish.")
                self.status = DroneBuildStatus.timeout
                return
            status = self.current_status()
            if status == 'success':
                logging.info("Build finished successfully.")
                self.status = DroneBuildStatus.success
                return
            elif status == 'failure' or status == 'error' or status == 'killed':
                logging.error(f"Build failed, status = {status}.")
                self.status = DroneBuildStatus.failure
                return
            elif status == 'pending':
                logging.info("Build is pending.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger a Drone CI build.")
    parser.add_argument('--log', type=str, default='INFO', help="Logging level.")
    parser.add_argument('--repo', type=str, required=True, help="Repository name.")
    parser.add_argument('--branch', type=str, required=False, help="Branch name.")
    parser.add_argument('--commit', type=str, required=False, help="Commit hash.")

    args = parser.parse_args()
    if args.log:
        loglevel = getattr(logging, args.log.upper(), None)
        logging.basicConfig(level=loglevel)

    DRONE_TOKEN: str|None = _setup_drone_token()
    if not DRONE_TOKEN:
        raise OSError('Cannot get DRONE_TOKEN from GCP secret manager or environment variable')
    drone_build = DroneBuild(repo=args.repo, branch=args.branch, commit=args.commit)
    drone_build.trigger()
    drone_build.wait_until_finished(timeout=600)
    if drone_build.status == DroneBuildStatus.success:
        logging.info("Build finished successfully.")
        exit(0)
    elif drone_build.status == DroneBuildStatus.failure:
        logging.error("Build failed.")
        exit(1)
    else:
        logging.error("Build timed out.")
        exit(2)
