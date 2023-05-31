from tortoise import models, fields


class TimestampedModel(models.Model):
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True
