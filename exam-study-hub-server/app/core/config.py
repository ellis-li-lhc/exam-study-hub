# 从 pydantic-settings 库导入两个工具：
# - BaseSettings：配置类的基类，能自动从环境变量 / .env 文件读取配置
# - SettingsConfigDict：用来告诉 BaseSettings 一些规则（比如去哪读 .env）
from pydantic_settings import BaseSettings, SettingsConfigDict


# 定义一个配置类，继承 BaseSettings。
# 注意：class 必须小写！（大写 Class 会报语法错误）
class Settings(BaseSettings):
    # 配置读取规则：
    # - env_file=".env"：从当前目录的 .env 文件读配置
    # - env_file_encoding="utf-8"：.env 文件用 utf-8 编码读取
    # - extra="ignore"：.env 里有多余的、类里没定义的变量时，忽略掉而不报错
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 数据库连接串。给了默认值，所以今天没有 .env、没有数据库也能启动。
    # 将来在 .env 里写同名的 DATABASE_URL，就会自动覆盖这个默认值。
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/exam_study"

    # 允许跨域访问的前端地址。前端 Vite 开发服务器默认跑在 5173 端口。
    cors_origins: str = "http://localhost:5173"

    # @property 让下面这个方法可以像属性一样访问：settings.cors_origin_list
    # 作用：把上面用逗号分隔的字符串，拆成一个列表，方便 CORS 中间件使用。
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# 创建一个全局配置实例。其他文件用 `from app.core.config import settings` 就能拿到。
settings = Settings()
