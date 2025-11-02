from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class Transaction(BaseModel):
    Date: date = Field(..., alias="Date")
    Amount: float = Field(..., alias="Amount")
    Payer_Name: Optional[str] = Field(None, alias="Payer Name")
    Receiver_Name: Optional[str] = Field(None, alias="Receiver Name")
    Description: Optional[str] = Field(None, alias="Description")
    Operation_Type: Optional[str] = Field(None, alias="Operation Type")
    Account_Subtype: Optional[str] = Field(None, alias="Account Subtype")
    Pluggly_Connectors_Name: Optional[str] = Field(None, alias="Pluggly Connectors Name")

    class Config:
        populate_by_name = True  
