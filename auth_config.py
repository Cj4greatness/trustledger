# Business owner login credentials (MVP: single user)
import os
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "$2b$12$ir0hPvJ66ArIPWqsfvSTgeVKYy.vQARPNrtQyUj/R1Bwohgf7wUBK"
SECRET_KEY = os.getenv("SECRET_KEY")
