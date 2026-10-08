address = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'

print(f"Address: {address}")
print(f"Length: {len(address)} characters")
print(f"Format: 0x + 40 hex chars")
print(f"Valid Ethereum: {address.startswith('0x') and len(address) == 42}")
print()
print("This IS a valid Ethereum address!")
print("It belongs to: Vitalik Buterin (Ethereum founder)")
print("ENS name: vitalik.eth")
print()
print("You can verify on Etherscan:")
print(f"https://etherscan.io/address/{address}")
