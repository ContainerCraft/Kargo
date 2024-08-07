"""A generated module for Kargo functions

This module has been generated via dagger init and serves as a reference to
basic module structure as you get started with Dagger.

Two functions have been pre-created. You can modify, delete, or add to them,
as needed. They demonstrate usage of arguments and return types using simple
echo and grep commands. The functions can be called from the dagger CLI or
from one of the SDKs.

The first line in this comment block is a short description line and the
rest is a long description with more detail on the module's purpose or usage,
if appropriate. All modules should have a short description.
"""

import dagger
from dagger import dag, function, object_type

# NOTE: it's recommended to move your code into other files in this package
# and keep __init__.py for imports only, according to Python's convention.
# The only requirement is that Dagger needs to be able to import a package
# called "main", so as long as the files are imported here, they should be
# available to Dagger.


@object_type
class Kargo:
    @function
    def container_echo(self, apt_command: str) -> str:
        """Returns a container that echoes whatever string argument is provided"""
        return dag.container().from_("ubuntu:22.04").with_exec(["apt", apt_command]).stdout()

    @function
    def konductor(self) -> str:
        """DOCS"""
        return dag.container().from_("ghcr.io/containercraft/konductor:latest").with_exec(["pulumi", "--version"]).stdout()

    @function
    def touchabc(self) -> dagger.Container:
        return dag.container().from_("golang:1").with_exec(["go", "version"])

    @function
    def whichgo(self) -> str:
        return self.touchabc().with_exec(["which", "go"]).stdout()

    @function
    def readabc(self) -> str:
        go_binary = self.touchabc().file("/usr/local/go/bin/go")
        return dag.container().from_("ubuntu:22.04").with_file("/usr/bin/go", go_binary).with_exec(["go", "version"]).stdout()

    @function
    def create_dind(self) -> dagger.Service:
        return dag.container().from_("docker:dind").with_exposed_port(2375).with_exec(insecure_root_capabilities=True,args=["dockerd", "--host", "tcp://0.0.0.0:2375"]).as_service()

    @function
    async def create_kind_cluster(self) -> str:
        service = self.create_dind()
        return await dag.container().from_("docker:dind").with_service_binding("dind", service).with_env_variable("DOCKER_HOST", "tcp://dind:2375").with_exec(["docker", "container", "run", "--rm", "hello-world"]).stdout()
