class TodoList(object):
    UNDONE = 0
    IN_PROGRESS = 1
    DONE = 2
    CANCEL = 3
    def __init__(self):
        self.todos = {}
        self.count = 0

    def _has_status(self, status):
        res = []
        for ident in self.todos:
            item = self.todos[ident]
            if item['status'] == status:
                res.append(item['item'])
        return res

    def _set_status(self, ident, status):
        if ident in self.todos:
            self.todos[ident]['status'] = status
        else:
            raise KeyError("Id: {} was not found in the todo list".format(ident))

    def add(self, item):
        self.todos[self.count] = {'status': TodoList.UNDONE, 'item': item}
        self.count += 1

    def next(self):
        for ident in self.todos:
            item = self.todos[ident]
            if item['status'] == TodoList.UNDONE:
                item['status'] = TodoList.IN_PROGRESS
                return ident, item['item']
        return None

    def abort(self, ident):
        self._set_status(ident, TodoList.UNDONE)

    def cancel(self, ident):
        self._set_status(ident, TodoList.CANCEL)

    def complete(self, ident):
        self._set_status(ident, TodoList.DONE)

    def size(self):
        return self.count

    def remaining(self):
        return self._has_status(TodoList.UNDONE)

    def completed(self):
        return self._has_status(TodoList.DONE)

    def in_progress(self):
        return self._has_status(TodoList.IN_PROGRESS)

    def cancelled(self):
        return self._has_status(TodoList.CANCEL)

