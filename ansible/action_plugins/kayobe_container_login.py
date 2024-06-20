from ansible.plugins.action import ActionBase

_engine_to_module = {
   'docker': 'community.docker.docker_login',
   'podman': 'containers.podman.podman_login'
}

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        module_args = self._task.args.copy()
        engine = task_vars.get("container_engine", "docker")
        module = _engine_to_module.get(engine)
        if engine == "podman":
            # Drop unspported arguments
            module_args.pop("reauthorize", None)
            # Rename arguments that differ from docker
            if module_args.get("registry_url"):
                module_args["registry"] = module_args["registry_url"]
                del module_args["registry_url"]
        module_return = self._execute_module(module_name=module,
                                             module_args=module_args,
                                             task_vars=task_vars, tmp=tmp)
        return module_return
