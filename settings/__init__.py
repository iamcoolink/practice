from datetime import timedelta


DB_URI = "mysql+aiomysql://root:sgwcl666@localhost:3306/make-name?charset=utf8mb4"

DEEPSEEK_API_KEY = "sk-9a72e672c67e429684bf0b12e4f75f1b"


# 邮箱相关配置
MAIL_USERNAME="3163198546@qq.com"
MAIL_PASSWORD="qqvhbrlewmpgdgaf"
MAIL_FROM="3163198546@qq.com"
MAIL_PORT=587
MAIL_SERVER="smtp.qq.com"
MAIL_FROM_NAME="项目"
MAIL_STARTTLS=True
MAIL_SSL_TLS=False



JWT_SECRET_KEY="abcdefgh"
JWT_ACCESS_TOKEN_EXPIRES=timedelta(days=15)  ##配置访问令牌（Access Token）的过期时间
JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=7) ##配置刷新令牌（Refresh Token）的过期时间

