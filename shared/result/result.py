from typing import List, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    """Represents the outcome of an operation.
    Attributes
    ----------
    success : bool
        A flag that is set to True if the operation was successful, False if
        the operation failed.
    value : object
        The result of the operation if successful, value is None if operation
        failed or if the operation has no return value.
    error : str
        Error message detailing why the operation failed, value is None if
        operation was successful.
    """

    def __init__(self, success: bool, value: T, error: E):
        if success and error:
            raise Exception("Can't have a succesfull result with error")
        if not success and value:
            raise Exception("Can't have an errored result with value")
        self.success: bool = success
        self.error: E = error
        self.value: T = value

    @property
    def failure(self):
        """True if operation failed, False if successful (read-only)."""
        return not self.success

    def __str__(self):
        if self.success:
            return f"[Success]"
        else:
            return f'[Failure] "{self.error}"'

    def __repr__(self):
        if self.success:
            return f"<Result success={self.success}>"
        else:
            return f'<Result success={self.success}, message="{self.error}">'

    @classmethod
    def Fail(cls, error):
        """Create a Result object for a failed operation."""
        return cls(False, value=None, error=error)

    @classmethod
    def Ok(cls, value=None):
        """Create a Result object for a successful operation."""
        return cls(True, value=value, error=None)

    @classmethod
    def combine(cls, result_list: List):
        acc = cls.Ok(value=[])
        for result in result_list:
            if acc.success:
                if result.success:
                    if type(result.value) is list:
                        acc.value.extend(result.value)
                    else:
                        acc.value.append(result.value)
                else:
                    acc = cls.Fail(result.error)
            else:
                break
        return acc
