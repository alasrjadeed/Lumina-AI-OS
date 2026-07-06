import pytest

from kernel.dependency.exceptions import ServiceRegistrationError
from kernel.dependency.lifetime import Lifetime
from kernel.dependency.provider import InstanceProvider, TypeProvider
from kernel.dependency.registry import ServiceRegistration, ServiceRegistry


class _Repo:
    pass


def test_register_and_get():
    reg = ServiceRegistry()
    r = ServiceRegistration(
        service="db",
        provider=InstanceProvider("conn"),
        lifetime=Lifetime.SINGLETON,
    )
    reg.register(r)
    assert reg.get("db") is r


def test_register_duplicate_raises():
    reg = ServiceRegistry()
    reg.register(
        ServiceRegistration(
            service="x",
            provider=InstanceProvider(1),
        ),
    )
    with pytest.raises(ServiceRegistrationError):
        reg.register(
            ServiceRegistration(
                service="x",
                provider=InstanceProvider(2),
            ),
        )


def test_has():
    reg = ServiceRegistry()
    assert reg.has("x") is False
    reg.register(
        ServiceRegistration(
            service="x",
            provider=InstanceProvider(1),
        ),
    )
    assert reg.has("x") is True


def test_remove():
    reg = ServiceRegistry()
    reg.register(
        ServiceRegistration(
            service="x",
            provider=InstanceProvider(1),
        ),
    )
    assert reg.remove("x") is True
    assert reg.remove("x") is False
    assert reg.has("x") is False


def test_clear():
    reg = ServiceRegistry()
    reg.register(
        ServiceRegistration(
            service="a",
            provider=InstanceProvider(1),
        ),
    )
    reg.register(
        ServiceRegistration(
            service="b",
            provider=InstanceProvider(2),
        ),
    )
    reg.clear()
    assert reg.has("a") is False
    assert reg.has("b") is False


def test_all():
    reg = ServiceRegistry()
    reg.register(
        ServiceRegistration(
            service="a",
            provider=InstanceProvider(1),
        ),
    )
    reg.register(
        ServiceRegistration(
            service="b",
            provider=InstanceProvider(2),
        ),
    )
    assert len(reg.all()) == 2


def test_find_by_tag():
    reg = ServiceRegistry()
    reg.register(
        ServiceRegistration(
            service="a",
            provider=InstanceProvider(1),
            tags={"cache", "private"},
        ),
    )
    reg.register(
        ServiceRegistration(
            service="b",
            provider=InstanceProvider(2),
            tags={"public"},
        ),
    )
    assert len(reg.find_by_tag("cache")) == 1
    assert len(reg.find_by_tag("public")) == 1
    assert len(reg.find_by_tag("missing")) == 0
