import ssl
import certifi

print("✅ Installing certificates from certifi...")
ssl_context = ssl.create_default_context(cafile=certifi.where())
print("✅ Certificate installation completed.")
