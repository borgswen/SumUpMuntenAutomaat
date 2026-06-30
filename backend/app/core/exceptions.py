from __future__ import annotations


class PaymentError(Exception):
    pass


class PaymentTimeout(PaymentError):
    pass


class HopperError(Exception):
    pass


class HopperJam(HopperError):
    pass


class HopperEmpty(HopperError):
    pass


class EmergencyStop(HopperError):
    pass


class ConfigurationError(Exception):
    pass
