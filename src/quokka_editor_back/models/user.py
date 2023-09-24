from tortoise import fields, models


class User(models.Model):
    id = fields.UUIDField(pk=True, index=True)
    username = fields.CharField(max_length=250, unique=True, index=True)
    email = fields.CharField(max_length=250, unique=True, index=True)
    first_name = fields.CharField(max_length=250, default="")
    last_name = fields.CharField(max_length=250, default="")
    hashed_password = fields.CharField(max_length=250)
    is_active = fields.BooleanField(default=False)
