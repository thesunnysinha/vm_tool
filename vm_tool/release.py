import subprocess
import yaml
import os
import shutil


class ReleaseManager:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def _log(self, message):
        if self.verbose:
            print(f"DEBUG: {message}")

    def merge_compose_files(self, files, output_file):
        """
        Merge multiple docker-compose files using `docker compose config`.
        """
        if not files:
            raise ValueError("No input files provided")

        cmd = ["docker", "compose"]
        for f in files:
            if not os.path.exists(f):
                # Fallback: check if it exists relative to current dir?
                # Or just skip/warn? For now, fail if explicit file missing.
                # But our logic handles missing optional files upstream.
                if self.verbose:
                    print(f"Warning: File {f} does not exist, skipping.")
                continue
            cmd.extend(["-f", f])

        cmd.append("config")

        self._log(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            with open(output_file, "w") as f:
                f.write(result.stdout)
            print(f"✅ Merged configuration written to {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error merging compose files: {e.stderr}")
            raise

    def fix_paths(
        self,
        file_path,
        target_pattern=r"/home/runner/work/[^/]*/[^/]*",
        replacement=".",
    ):
        """
        Replace absolute CI paths with relative paths.
        Uses sed-like logic but in Python.
        """
        import re

        with open(file_path, "r") as f:
            content = f.read()

        # Regex replacement
        new_content = re.sub(target_pattern, replacement, content)

        if content != new_content:
            with open(file_path, "w") as f:
                f.write(new_content)
            print(f"✅ Fixed paths in {file_path}")
        else:
            self._log("No path replacements needed.")

    def strip_service_volumes(self, file_path, service_name):
        """
        Load YAML, remove 'volumes' from the specified service, and write back.
        Also remove nginx-specific hardcoded volume keys like 'nginx.conf' if present
        in a way that pyyaml doesn't mess up.
        Actually, let's use a pure YAML approach.
        """
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        services = data.get("services", {})
        if service_name in services:
            service = services[service_name]
            if "volumes" in service:
                del service["volumes"]
                print(f"✅ Stripped volumes from service '{service_name}'")

                # Write back
                with open(file_path, "w") as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                self._log(f"Service '{service_name}' has no volumes to strip.")
        else:
            self._log(f"Service '{service_name}' not found in compose file.")

    def prepare_release(
        self, base_file, prod_file, output_file, strip_volumes=None, fix_paths=True
    ):
        """
        Orchestrate the release preparation.
        """
        files_to_merge = []
        if os.path.exists(base_file):
            files_to_merge.append(base_file)

        # Check prod file variants
        if os.path.exists(prod_file):
            files_to_merge.append(prod_file)
        elif os.path.exists(os.path.basename(prod_file)):
            files_to_merge.append(os.path.basename(prod_file))

        if not files_to_merge:
            raise FileNotFoundError("No valid docker-compose files found to merge.")

        self.merge_compose_files(files_to_merge, output_file)

        if fix_paths:
            self.fix_paths(output_file)

        if strip_volumes:
            for svc in strip_volumes.split(","):
                self.strip_service_volumes(output_file, svc.strip())
