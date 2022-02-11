from flask import Flask, render_template, redirect, abort, flash, url_for, request, abort
from flaskwebgui import FlaskUI
from dotenv import load_dotenv
import requests
import os
from Raspi_Gui import models as mdls
from Raspi_Gui import func
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import pandas as pd
import matplotlib.pyplot as plt