from tortoise.fields.data import BooleanField, CharField, IntField, TextField
from tortoise.models import Model


class BaseModel(Model):
    @classmethod
    def get_(cls, *args, **kwargs):
        super().get(*args, **kwargs)

    @classmethod
    def get(cls, **kwargs):
        return cls.filter(**kwargs)

    @classmethod
    async def add(cls, q=None, **kwargs):
        if q is None: # 没设置查询参数时尝试使用主键查询
            pk_name = cls.describe()["pk_field"]["name"]
            if pk_name == "id" and pk_name not in kwargs: # tortoise.未设置主键时默认主键名为id
                filters = kwargs
            else:
                filters = {pk_name: kwargs[pk_name]}
        else:
            filters = q
        if await cls.get(**filters).exists():
            return False
        await cls.create(**kwargs)
        return True

    @classmethod
    async def delete(cls, **kwargs):
        query = cls.get(**kwargs)
        if await query.exists():
            await query.delete()
            return True
        return False

    @classmethod
    async def update(cls, q, **kwargs):
        query = cls.get(**q)
        if await query.exists():
            await query.update(**kwargs)
            return True
        return False

    class Meta:
        abstract = True

# TODO 自定义默认权限
class Sub(BaseModel):
    type = CharField(max_length=10)
    type_id = IntField()
    uid = IntField()
    live = BooleanField()  # default=True
    dynamic = BooleanField()  # default=True
    at = BooleanField()  # default=False
    bot_id = IntField()
    live_tips = CharField(max_length=100)

class Sub_dy(BaseModel):
    """抖音订阅"""
    group_id = IntField()
    bot_id = IntField()
    sec_uid = CharField(max_length=100)
    name = CharField(max_length=100) # 冗余存储仅用来方便查看

class User(BaseModel):
    uid = IntField(pk=True)
    name = CharField(max_length=20)

class User_dy(BaseModel):
    sec_uid = CharField(max_length=100, pk=True)
    name = CharField(max_length=100)
    room_id = IntField(default=0)
    live_url = CharField(max_length=100)

class Group(BaseModel):
    # tortoise 不支持复合主键，因此只能代码里不设置主键(tortoise会自动创建一个名为id的自增列作为主键)
    group_id = IntField() # pk=True
    bot_id = IntField() # pk=True
    admin = BooleanField(default=True)  # default=True
    decrease_notice = BooleanField(default=True) # default=True
    chatgpt = BooleanField(default=False) # default=False
    bili_summary = BooleanField(default=False) # default=True

class Guild(BaseModel):
    bot_id = IntField() # pk=True
    guild_id = TextField() # pk=True
    channel_id = TextField() # pk=True
    admin = BooleanField(default=True)  # default=True
    decrease_notice = BooleanField(default=True) # default=True
    chatgpt = BooleanField(default=False) # default=False
    bili_summary = BooleanField(default=True) # default=True


class Version(BaseModel):
    version = CharField(max_length=30)


# class Login(BaseModel):
#     uid = IntField(pk=True)
#     data = JSONField()
#     expireed = IntField()
