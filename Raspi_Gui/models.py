import os
import requests
from flask_wtf import FlaskForm
from wtforms import SubmitField
from dataclasses import dataclass
from flask_login import UserMixin
import pandas as pd
from wtforms.validators import Length, EqualTo, DataRequired, Email, ValidationError
from wtforms import StringField, EmailField, PasswordField, SubmitField, IntegerField

MAIN_URL = "http://192.168.1.111:4000"

@dataclass
class Stall(UserMixin):
    Stall_ID: int
    Name: str
    Password: str
    Account: str
    Phone: str

    @classmethod
    def retrieve_info(cls: object, ID_Stall: int, Account: str, Password: str, Link: str):
        if ID_Stall == 0 or Account == 0:
            return -1
        df = pd.read_html(f'{Link}/query/cmd=STALL&{ID_Stall}&{Account}&{Password}')[0]
        if df.size == 0:
            return -1
        
        df = df.drop(df.columns[0], axis=1).values[0]
        return cls(*df)

    def register(self, Link: str):
        url = f'{Link}/update/cmd=REGISTERSTALL&0&{self.Name}&{self.Password}&{self.Account}&{self.Phone}'
        code = requests.get(url)
        if code.status_code == 200:
            return 0
        return -1

    @staticmethod
    def update_order(Link: str, ID_ORDER: int, STATUS: str):
        url = f'{Link}/update/cmd=UPDATEORDER&{ID_ORDER}&{STATUS}'
        code = requests.get(url)
        if code.status_code == 200:
            return 0
        return -1

    @staticmethod
    def cancel_order(Link: str, ID_ORDER: int):
        url = f'{Link}/delete/cmd=ORDERS&{ID_ORDER}'
        code = requests.get(url)
        if code.status_code == 200:
            return 0
        return -1

    @staticmethod
    def BOX_STATUS(Link: str, ID_Stall: int):
        url = f'{Link}/query/cmd=STALL_BOX_QUERY&{ID_Stall}'
        df = pd.read_html(url)[0]
        df = df.drop(df.columns[0], axis=1)
        return df

    @staticmethod
    def UPDATE_ORDER_BOX(Link: str, ID_BOX: int, ID_ORDER: int):
        url = f'{Link}/update/cmd=UPDATE_ORDER_BOX&{ID_BOX}&{ID_ORDER}'
        code = requests.get(url)
        if code.status_code == 200:
            return 0
        return -1

    @staticmethod
    def VIEW_CUSTOMER_ORDER(Link: str, ID_Customer: int):
        url = f'{Link}/query/cmd=CUSTOMER_ORDERS&{ID_Customer}'
        df = pd.read_html(url)[0]
        df = df.drop(df.columns[0], axis=1)
        return df
    
    def is_authenticated(self):
        return super().is_authenticated

    def get_id(self):
        return self.Stall_ID


class AcceptForm(FlaskForm):
    Accept = SubmitField(label="Accept")  # SWITCHES TO PREPARING
    Deny = SubmitField(label="Deny")  # SWTICHES TO CANCEL THE ORDER
    Done = SubmitField(label="Done")  # SWITCHES TO READY
    Verify = SubmitField(label="Verify Any Orders ✅")

class Finish_Order(FlaskForm):
    Paid = SubmitField(label="Paid, Present and Accounted For")

class ALLOCATE(FlaskForm):
    Allocate = SubmitField(label="Allocate Order")
    Release = SubmitField(label="Release Order")

class Signup(FlaskForm):
    Name = StringField(label="UserName", validators=[DataRequired()])
    Password = StringField(label="Password", validators=[DataRequired()])
    Account = StringField(label="Account", validators=[DataRequired()])
    Phone = StringField(label="Phone", validators=[DataRequired()])
    Submit = SubmitField(label="Sign Up")

    def validate_Account(self, Account: str):
        res = requests.get(f'{MAIN_URL}/cmd=REGISTER_NAME&{Account}').text
        if res == "True":
            raise ValidationError
        return 0