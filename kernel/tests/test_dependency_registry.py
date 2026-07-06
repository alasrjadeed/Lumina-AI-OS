import pytest

from kernel.dependency.exceptions import ServiceRegistrationError
from kernel.dependency.lifetime import Lifetime
from kernel.dependency.provider import InstanceProvider, TypeProvider
from kernel.dependency.models import ServiceRegistration
from kernel.dependency.registry import ServiceRegistry


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


def test_keys():
    reg = ServiceRegistry()
    reg.register(ServiceRegistration(service="a", provider=InstanceProvider(1)))
    reg.register(ServiceRegistration(service="b", provider=InstanceProvider(2)))
    keys = reg.keys()
    assert "a" in keys
    assert "b" in keys


def test_count():
    reg = ServiceRegistry()
    assert reg.count() == 0
    reg.register(ServiceRegistration(service="a", provider=InstanceProvider(1)))
    assert reg.count() == 1
    reg.register(ServiceRegistration(service="b", provider=InstanceProvider(2)))
    assert reg.count() == 2


def test_register_or_replace_new():
    reg = ServiceRegistry()
    r = ServiceRegistration(service="x", provider=InstanceProvider(1))
    existed = reg.register_or_replace(r)
    assert existed is False
    assert reg.get("x") is r


def test_register_or_replace_existing():
    reg = ServiceRegistry()
    r1 = ServiceRegistration(service="x", provider=InstanceProvider(1))
    r2 = ServiceRegistration(service="x", provider=InstanceProvider(2))
    reg.register(r1)
    existed = reg.register_or_replace(r2)
    assert existed is True
    assert reg.get("x") is r2


def test_bulk_register():
    reg = ServiceRegistry()
    reg.bulk_register([
        ServiceRegistration(service="a", provider=InstanceProvider(1)),
        ServiceRegistration(service="b", provider=InstanceProvider(2)),
    ])
    assert reg.count() == 2
    assert reg.has("a")
    assert reg.has("b")


def test_bulk_register_duplicate_raises():
    reg = ServiceRegistry()
    reg.register(ServiceRegistration(service="a", provider=InstanceProvider(1)))
    with pytest.raises(ServiceRegistrationError):
        reg.bulk_register([
            ServiceRegistration(service="a", provider=InstanceProvider(2)),
        ])


def test_find_by_lifetime():
    reg = ServiceRegistry()
    reg.register(ServiceRegistration(
        service="s1", provider=InstanceProvider(1), lifetime=Lifetime.SINGLETON,
    ))
    reg.register(ServiceRegistration(
        service="s2", provider=InstanceProvider(2), lifetime=Lifetime.SCOPED,
    ))
    reg.register(ServiceRegistration(
        service="t1", provider=InstanceProvider(3), lifetime=Lifetime.TRANSIENT,
    ))
    assert len(reg.find_by_lifetime(Lifetime.SINGLETON)) == 1
    assert len(reg.find_by_lifetime(Lifetime.SCOPED)) == 1
    assert len(reg.find_by_lifetime(Lifetime.TRANSIENT)) == 1
