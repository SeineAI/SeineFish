import yaml
import subprocess
import os
import sys
import shutil


def detect_container_runtime():
    """
    Detects if Docker or Podman is installed and returns the container runtime.

    Returns:
        str: The container runtime to use ('docker' or 'podman').

    Raises:
        SystemExit: If neither Docker nor Podman is installed.
    """
    if shutil.which('podman'):
        return 'podman'
    elif shutil.which('docker'):
        return 'docker'
    else:
        print("Neither Docker nor Podman is installed.")
        exit(1)


def load_workflow(file_path):
    """
    Load the workflow from a YAML file.

    Args:
        file_path (str): The path to the workflow YAML file.

    Returns:
        dict: The loaded workflow as a dictionary.
    """
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def run_command_in_container(command, container_id, step_name, job_name,
                             output_dir, runtime):
    """
    Run a command in a container and save the output to a file.

    Args:
        command (str): The command to run.
        container_id (str): The ID of the container.
        step_name (str): The name of the step being executed.
        job_name (str): The name of the job being executed.
        output_dir (str): The directory to save the output files.
        runtime (str): The container runtime to use ('docker' or 'podman').

    Raises:
        SystemExit: If the command fails, exits the program with an error code.
    """
    result = subprocess.run(
        f"{runtime} exec {container_id} /bin/bash -c '{command}'",
        shell=True,
        capture_output=True,
        text=True)
    output_file = os.path.join(output_dir, f"{job_name}_{step_name}.txt")
    with open(output_file, 'w') as f:
        f.write(result.stdout)
        if result.returncode != 0:
            f.write(f"\nError: {result.stderr}")
            print(f"Command failed with error: {result.stderr}")
            exit(result.returncode)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Step '{step_name}' failed with error: {result.stderr}")
        exit(result.returncode)


def run_step_in_container(step, container_id, job_name, output_dir, runtime):
    """
    Run a step in a container.

    Args:
        step (dict): The step to run, as a dictionary.
        container_id (str): The ID of the container.
        job_name (str): The name of the job being executed.
        output_dir (str): The directory to save the output files.
        runtime (str): The container runtime to use ('docker' or 'podman').
    """
    print(f"Running step: {step['name']}")
    commands = step['run'].strip().split('\n')
    for command in commands:
        run_command_in_container(command, container_id, step['name'], job_name,
                                 output_dir, runtime)


def run_job_in_container(job, image, job_name, output_dir, runtime):
    """
    Run a job in a container.

    Args:
        job (dict): The job to run, as a dictionary.
        image (str): The container image to use.
        job_name (str): The name of the job being executed.
        output_dir (str): The directory to save the output files.
        runtime (str): The container runtime to use ('docker' or 'podman').
    """
    print(f"Running job in container: {job_name}")

    # Prepare bind mounts
    binds = " ".join([
        f"-v {mount['host']}:{mount['container']}"
        for mount in job.get('bind-mounts', [])
    ])

    # Prepare environment variables
    env_vars = " ".join(
        [f"-e {key}={value}" for key, value in job.get('env', {}).items()])

    # Run the container with the specified image, bind mounts, and environment variables
    container_id = subprocess.check_output(
        f"{runtime} run -d -it {binds} {env_vars} {image} /bin/bash",
        shell=True,
        text=True).strip()
    for step in job['steps']:
        run_step_in_container(step, container_id, job_name, output_dir,
                              runtime)
    subprocess.run(f"{runtime} stop {container_id}", shell=True)
    subprocess.run(f"{runtime} rm {container_id}", shell=True)


def main():
    """
    Main function to run the workflow runner. It loads the workflow file,
    runs the jobs specified in the workflow, and handles the execution
    environment for each job.

    Usage:
        python workflow_runner.py <workflow_file>

    Raises:
        SystemExit: If the workflow file is not provided or if an unsupported
                    environment is specified.
    """
    if len(sys.argv) < 2:
        print("Usage: python workflow_runner.py <workflow_file>")
        exit(1)

    workflow_file = sys.argv[1]
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    workflow = load_workflow(workflow_file)
    jobs = workflow['jobs']

    runtime = detect_container_runtime()
    print(f"Using container runtime: {runtime}")

    for job_name, job in jobs.items():
        if job['runs-on'] == 'container':
            runtime_to_use = job.get('container-runtime', runtime)
            run_job_in_container(job, job['container-image'], job_name,
                                 output_dir, runtime_to_use)
        else:
            print(f"Unsupported environment: {job['runs-on']}")


if __name__ == "__main__":
    main()
