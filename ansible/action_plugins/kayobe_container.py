from ansible.plugins.action import ActionBase

_engine_to_module = {
   'docker': 'community.docker.docker_container',
   'podman': 'containers.podman.podman_container'
}

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        module_args = self._task.args.copy()
        engine = task_vars.get("container_engine", "docker")
        if engine == "podman":
            auto_remove = module_args.pop('cleanup', None)
            if auto_remove:
                module_args["auto_remove"] = True
            # TODO(wszumski): Drop unsupported arguments. In the future
            # we could emulate these options.
            module_args.pop('timeout', None)
            module_args.pop('comparisons', None)
        module = _engine_to_module.get(engine)
        module_return = self._execute_module(module_name=module,
                                             module_args=module_args,
                                             task_vars=task_vars, tmp=tmp)
        return module_return
