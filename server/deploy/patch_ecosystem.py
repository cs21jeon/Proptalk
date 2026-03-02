"""패치: ecosystem.config.js에 GOOGLE_CLIENT_SECRET 추가, ENABLE_DRIVE_BACKUP 활성화"""

filepath = "/home/webapp/goldenrabbit/chat_stt/server/ecosystem.config.js"

with open(filepath, "r") as f:
    content = f.read()

# 1) ENABLE_DRIVE_BACKUP: 'false' → 'true'
content = content.replace("ENABLE_DRIVE_BACKUP: 'false'", "ENABLE_DRIVE_BACKUP: 'true'")

# 2) GOOGLE_CLIENT_SECRET 추가 (GOOGLE_CLIENT_ID 줄 다음에)
if 'GOOGLE_CLIENT_SECRET' not in content:
    content = content.replace(
        "GOOGLE_CLIENT_ID: '325885879870-rj00lod4843dj8qrt9gjnrpcfmsltc9v.apps.googleusercontent.com',",
        "GOOGLE_CLIENT_ID: '325885879870-rj00lod4843dj8qrt9gjnrpcfmsltc9v.apps.googleusercontent.com',\n      GOOGLE_CLIENT_SECRET: process.env.GOOGLE_CLIENT_SECRET || '',",
    )

with open(filepath, "w") as f:
    f.write(content)

print("OK - ecosystem.config.js updated (ENABLE_DRIVE_BACKUP=true, GOOGLE_CLIENT_SECRET added)")
