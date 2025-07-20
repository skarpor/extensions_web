# ==================== 预定义权限验证函数 ====================

from core.auth import require_permissions,require_any_permission



# 系统管理权限
manage_system = require_permissions("system:manage")
manage_logs = require_permissions("system:logs")
view_settings = require_permissions("settings:view")
update_settings = require_permissions("settings:update")

# 用户管理权限
manage_users = require_permissions("user:create", "user:update", "user:delete")
create_users = require_permissions("user:create")
view_users = require_permissions("user:read")
update_users = require_permissions("user:update")
delete_users = require_permissions("user:delete")

# 角色权限管理
manage_roles = require_permissions("role:create","role:read","role:update","role:delete")
create_roles = require_permissions("role:create")
view_roles = require_permissions("role:read")
update_roles = require_permissions("role:update")
delete_roles = require_permissions("role:delete")
assign_roles = require_permissions("role:assign")
# 数据库、表管理权限
manage_database = require_permissions("database:manage")
view_database = require_permissions("database:view")
update_database = require_permissions("database:update")
delete_database = require_permissions("database:delete")
view_table_p = require_permissions("table:view")
update_table_p = require_permissions("table:update")
delete_table_p = require_permissions("table:delete")

# 文件管理权限
manage_files = require_permissions("file:manage")
upload_files = require_permissions("file:upload")
download_files = require_permissions("file:download")
view_files = require_permissions("file:view")
delete_files = require_permissions("file:delete")
# 文件夹管理
create_dir = require_permissions("file:createdir")
delete_dir = require_permissions("file:deletedir")

# 扩展管理权限
manage_extensions = require_permissions(
    "extension:view",
    "extension:upload",
    "extension:update",
    "extension:delete",
    "extension:execute",
    "extension:config",
)
upload_extensions = require_permissions("extension:upload")
view_extensions = require_permissions("extension:view")
update_extensions = require_permissions("extension:update")
delete_extensions = require_permissions("extension:delete")
query_extensions = require_permissions("extension:execute")
config_extensions = require_permissions("extension:config")

# 聊天管理权限
manage_chats = require_permissions(
    "chat:create",
    "chat:delete"
    "chat:update"
    "chat:read"
)
create_chats = require_permissions("chat:create")
view_chats = require_permissions("chat:read")
update_chats = require_permissions("chat:update")
delete_chats = require_permissions("chat:delete")

# 现代化聊天室权限
create_chat_rooms = require_permissions("chat:create")
view_chat_rooms = require_permissions("chat:read")
update_chat_rooms = require_permissions("chat:update")
delete_chat_rooms = require_permissions("chat:delete")
manage_chat_rooms = require_permissions("chat:room")
send_chat_messages = require_permissions("chat:message")
join_chat_rooms = require_permissions("chat:read")
search_chat_rooms = require_permissions("chat:read")

# 消息管理权限
manage_messages = require_permissions("message:create", "message:update", "message:delete")
create_messages = require_permissions("message:create")
view_messages = require_permissions("message:read")
update_messages = require_permissions("message:update")
delete_messages = require_permissions("message:delete")

# 日志权限
# view_logs = require_permissions("log:read")

# 帮助文档权限
view_help = require_permissions("help:view")
delete_help = require_permissions("help:delete")
upload_help = require_permissions("help:upload")
download_help = require_permissions("help:download")
list_help = require_permissions("help:list")

# 二维码文件权限
manage_qrfile = require_permissions(
    "qrfile:create",
    "qrfile:serialize",
    "qrfile:restore",
    "qrfile:download",
    "qrfile:download",
)
create_qrfile = require_permissions("qrfile:create")
serialize_qrfile = require_permissions("qrfile:read")
restore_qrfile = require_permissions("qrfile:delete")
download_qrfile = require_permissions("qrfile:download")

# 调度器权限
manage_scheduler = require_permissions(
    "scheduler:create",
    "scheduler:read",
    "scheduler:update",
    "scheduler:delete",
    "scheduler:execute",
    "scheduler:resume",
    "scheduler:pause",
)
create_scheduler = require_permissions("scheduler:create")
view_scheduler = require_permissions("scheduler:read")
update_scheduler = require_permissions("scheduler:update")
delete_scheduler = require_permissions("scheduler:delete")
execute_scheduler = require_permissions("scheduler:execute")
resume_scheduler = require_permissions("scheduler:resume")
pause_scheduler = require_permissions("scheduler:pause")
# 组合权限验证
file_read_write = require_any_permission("file:upload", "file:download", "file:view")
extension_read_write = require_any_permission("extension:upload", "extension:view", "extension:update")


# markdown
delete_markdown = require_permissions("markdown:delete")
view_markdown = require_permissions("markdown:view")
create_markdown = require_permissions("markdown:create")
list_markdown = require_permissions("markdown:list")
update_markdown = require_permissions("markdown:update")

