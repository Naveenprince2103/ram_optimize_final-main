from abc import ABC, abstractmethod

class BaseVault(ABC):
    @abstractmethod
    def mount(self, size: str, mount_point: str = None) -> bool:
        """Mount the RAM drive."""
        pass

    @abstractmethod
    def unmount(self, mount_point: str = None) -> bool:
        """Unmount the RAM drive."""
        pass

    @abstractmethod
    def panic(self) -> bool:
        """Emergency wipe and unmount."""
        pass
