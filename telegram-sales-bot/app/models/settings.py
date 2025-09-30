from sqlalchemy import Column, Integer, String, Text, Boolean, JSON
from .base import Base, TimestampMixin


class BotSettings(Base, TimestampMixin):
    __tablename__ = "bot_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String, default="string")  # string, int, float, bool, json
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)  # For hiding in UI
    category = Column(String, default="general")
    
    # Payment gateway credentials
    payment_gateway_config = Column(JSON)
    
    @property
    def typed_value(self):
        """Get value with correct type"""
        if self.value is None:
            return None
            
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        elif self.value_type == "json":
            import json
            return json.loads(self.value)
        else:
            return self.value
    
    @typed_value.setter
    def typed_value(self, value):
        """Set value with correct type conversion"""
        if value is None:
            self.value = None
        elif self.value_type == "json":
            import json
            self.value = json.dumps(value)
        else:
            self.value = str(value)
    
    def __repr__(self):
        return f"<BotSettings(id={self.id}, key={self.key}, category={self.category})>"
