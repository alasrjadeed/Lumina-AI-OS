from kernel.events.topic_matcher import TopicMatcher


def test_exact_match():
    assert TopicMatcher.matches("plugin.loaded", "plugin.loaded")


def test_global_star():
    assert TopicMatcher.matches("*", "anything")
    assert TopicMatcher.matches("*", "")
    assert TopicMatcher.matches("*", "kernel.started")


def test_prefix_wildcard():
    assert TopicMatcher.matches("browser.*", "browser.started")
    assert TopicMatcher.matches("browser.*", "browser.closed")
    assert TopicMatcher.matches("browser.*", "browser.tab.created")
    assert TopicMatcher.matches("browser.*", "browser.tab.closed")


def test_nested_prefix_wildcard():
    assert TopicMatcher.matches("browser.tab.*", "browser.tab.created")
    assert TopicMatcher.matches("browser.tab.*", "browser.tab.closed")


def test_nested_prefix_not_matches_shallower():
    assert not TopicMatcher.matches("browser.tab.*", "browser.started")
    assert not TopicMatcher.matches("browser.tab.*", "browser.closed")


def test_different_prefix_not_match():
    assert not TopicMatcher.matches("seo.*", "browser.started")
    assert not TopicMatcher.matches("voice.*", "crm.lead.created")


def test_exact_not_match():
    assert not TopicMatcher.matches("plugin.loaded", "plugin.unloaded")


def test_prefix_matches_root_topic():
    assert TopicMatcher.matches("kernel.*", "kernel")


def test_multiple_dot_levels():
    assert TopicMatcher.matches("a.*", "a.b.c.d")


def test_empty_subscription():
    assert not TopicMatcher.matches("", "anything")


def test_topic_longer_than_prefix():
    assert TopicMatcher.matches("crm.*", "crm.lead.created")
    assert TopicMatcher.matches("crm.*", "crm.followup.sent")
