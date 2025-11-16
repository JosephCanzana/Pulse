from helpers import *

password = generate_password_hash("mcmY_1946")

result =check_password("AdminPass_1","scrypt:32768:8:1$QwMDSjGCa4LlIVnC$7bc8add45125f055440e7ae652b28304382837f083e9a455f0ed29d32e3503b638702e7d0d6f8a8d91a7ac030d6ff5c913e61129515d277f8980a34adfde551e")
print("result",result)
print("generated pass: ",password)