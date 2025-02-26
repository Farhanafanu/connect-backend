from rest_framework import serializers
from user.models import CustomUser

class  AdminCustomSerializers(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=['id','email','password','username','is_active']
        extra_kwargs={
            'password':{'write_only':True}
        }
        def create(self,validated_data):
            password=validated_data.pop('password',None)
            instance=self.Meta.model(**validated_data)
            if password is not None:
                instance.set_password(password)
            instance.save()
            return instance

