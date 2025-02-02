from ansible.plugins.action import ActionBase

_engine_to_module = {
   'docker': 'community.docker.docker_image_info',
   'podman': 'containers.podman.podman_image_info'
}

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        module_args = self._task.args.copy()
        engine = task_vars.get("container_engine", "docker")
        module = _engine_to_module.get(engine)
        module_return = self._execute_module(module_name=module,
                                             module_args=module_args,
                                             task_vars=task_vars, tmp=tmp)
        return module_return
