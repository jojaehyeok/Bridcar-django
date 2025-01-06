from nested_admin import NestedModelAdmin, NestedStackedInline


def check_modifiable_requesting_status(requesting_history=None):
    if requesting_history is not None:
        if requesting_history.status == 'DONE':
            # @TODO: 일단 조건에 당근마켓 오더인 경우만 추가 해놨음
            if hasattr(requesting_history, 'daangn_requesting_information'):
                return False

    return True


def requesting_history_path_getter(requesting_history_path=''):
    def wrapper(wrapped):
        def get_requesting_history_object(self, obj):
            requesting_history = obj

            if requesting_history_path is not None:
                splitted_path = requesting_history_path.split('.')

                for path in splitted_path:
                    requesting_history = getattr(requesting_history, path)

            return requesting_history

        wrapped.get_requesting_history_object = get_requesting_history_object

        return wrapped
    return wrapper


class DisableModifyByRequestingStatusMixin(NestedStackedInline):
    def get_requesting_history(self, obj):
        requesting_history = obj

        if hasattr(self, 'get_requesting_history_object'):
            requesting_history = self.get_requesting_history_object(obj)

        return requesting_history

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            requesting_history = self.get_requesting_history(obj)

            if not check_modifiable_requesting_status(requesting_history):
                return False

        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            requesting_history = self.get_requesting_history(obj)

            return check_modifiable_requesting_status(requesting_history)

        return super().has_delete_permission(request, obj=obj)


