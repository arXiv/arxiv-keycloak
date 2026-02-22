from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EmailRecord")


@_attrs_define
class EmailRecord:
    """
    Attributes:
        timestamp (str):
        subject (str):
        headers (str):
        mail_from (str):
        mail_to (str):
        body (str):
        id (int):
    """

    timestamp: str
    subject: str
    headers: str
    mail_from: str
    mail_to: str
    body: str
    id: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        timestamp = self.timestamp

        subject = self.subject

        headers = self.headers

        mail_from = self.mail_from

        mail_to = self.mail_to

        body = self.body

        id = self.id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "timestamp": timestamp,
                "subject": subject,
                "headers": headers,
                "mail_from": mail_from,
                "mail_to": mail_to,
                "body": body,
                "id": id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        timestamp = d.pop("timestamp")

        subject = d.pop("subject")

        headers = d.pop("headers")

        mail_from = d.pop("mail_from")

        mail_to = d.pop("mail_to")

        body = d.pop("body")

        id = d.pop("id")

        email_record = cls(
            timestamp=timestamp,
            subject=subject,
            headers=headers,
            mail_from=mail_from,
            mail_to=mail_to,
            body=body,
            id=id,
        )

        email_record.additional_properties = d
        return email_record

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
