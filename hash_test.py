from helpers import *

password = generate_password_hash("mcmY_1946")

result =check_password("mcmY_1946","scrypt:32768:8:1$zQ90TifUV57h28Bl$f4b4c07b635d072c608d5191a3cabf224f5aaae76c8ef657712ee5263305a4e550a857aeb682d3ba6f619c8793c1cd16edfad820900bf93a532d59259d5b8664")
print("result",result)
print("generated pass: ",password)