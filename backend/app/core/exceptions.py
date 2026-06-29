from __future__ import annotations


class PaymentError(Exception):
    pass


class PaymentTimeout(PaymentError):
    pass


class HopperError(Exception):
    pass


class HopperJam(HopperError):
    pass


class ConfigurationError(Exception):
    pass
