import os
import sermonaudio
from dotenv import load_dotenv
from sermonaudio.node.requests import Node

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'))
SA_API_KEY= os.getenv('SA_API_KEY')


