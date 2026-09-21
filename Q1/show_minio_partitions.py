from minio import Minio

client = Minio("localhost:9000", access_key="admin", secret_key="admin12345", secure=False)
objects = client.list_objects("annapurna-lake", recursive=True)

print("="*75)
print("MINIO OBJECT STORAGE: BUCKET 'annapurna-lake' PARTITION STRUCTURE")
print("="*75)
partitions = []
total_size = 0
for obj in objects:
    partitions.append((obj.object_name, obj.size))
    total_size += obj.size

# Show first 20 partitions
print(f"Total Partitions Landed: {len(partitions)}")
print(f"Total Data Volume: {total_size / (1024*1024):.2f} MB\n")
print(f"{'Partition Path / Object Key':<60} | {'Size (KB)'}")
print("-" * 75)
for name, sz in partitions[:15]:
    print(f"{name:<60} | {sz/1024:.2f} KB")
print(f"{'...':<60} | ...")
for name, sz in partitions[-10:]:
    print(f"{name:<60} | {sz/1024:.2f} KB")
print("-" * 75)
