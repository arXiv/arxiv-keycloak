"""Trigger a build on a drone server and wait for it to finish."""

import argparse
import logging
import os
import time

import requests

DRONE_SERVER = os.environ.get('DRONE_SERVER', 'https://drone.arxiv.org')
if not os.environ.get('DRONE_TOKEN'):
    raise OSError('Missing DRONE_TOKEN environment variable')
DRONE_TOKEN = os.environ['DRONE_TOKEN']

class DroneBuild:
    """Class to trigger a build on a drone server and wait for it to finish."""

    def __init__(self, repo, namespace="arXiv", branch=None, commit=None) -> None:
        self.repo: str = repo
        self.namespace: str = namespace
        self.branch: str = branch
        self.commit: str = commit
        self.nr: int|None = None

    def _send_request(self, component, method='GET', params=None):
        """Send a request to the Drone API.

        Args:
            component (str): The API sub-component (after /api/repos/NS/REPO/) to call.
            method (str): The HTTP method to use (GET, POST).
            params (dict): The parameters to send with the request.
        """
        url = f"{DRONE_SERVER}/api/repos/{self.namespace}/{self.repo}/{component}"
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


    def is_running(self) -> bool:
        """Check if the build is currently running."""
        if self.nr is None:
            raise ValueError("Build number is not set. Trigger the build first.")
        response = self._send_request(f"builds/{self.nr}", method='GET')
        status = response.json()['status']
        logging.debug(f"Build status: {status}")
        return status == 'running'


    def wait_until_finished(self, timeout=600) -> None:
        """Wait until the build is finished."""
        if self.nr is None:
            raise ValueError("Build number is not set. Trigger the build first.")

        budget = timeout
        while self.is_running():
            logging.debug("Waiting for build to finish...")
            time.sleep(10)
            budget -= 10
            if budget <= 0:
                # TODO should we try to stop the build?
                logging.error("Timeout waiting for build to finish.")
                raise TimeoutError("Timeout waiting for build to finish.")


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

    drone_build = DroneBuild(repo=args.repo, branch=args.branch, commit=args.commit)
    drone_build.trigger()
    drone_build.wait_until_finished(timeout=600)
    logging.info("Build finished.")

