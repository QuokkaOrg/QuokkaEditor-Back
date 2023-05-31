from tortoise import models, fields


class Document(models.Model):
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=250)
    content = fields.BinaryField()
