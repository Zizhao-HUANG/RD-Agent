import os

# --- [极度重要] 终极诊断脚本输出的所有损坏文件完整路径 ---
FILES_TO_DELETE = [
    "git_ignore_folder/RD-Agent_workspace/93a0904acb114d308254fd606bad179b/result.h5",
    "git_ignore_folder/RD-Agent_workspace/f095de79271f4340bd004b3950cbc604/result.h5",
    "git_ignore_folder/RD-Agent_workspace/be727335a61d440f83d865b338f65c20/result.h5",
    "git_ignore_folder/RD-Agent_workspace/beca20265703481b8702ca50c7a1c878/result.h5",
    "git_ignore_folder/RD-Agent_workspace/1d084c11004745f5ad8ab9bca417537c/result.h5",
    "git_ignore_folder/RD-Agent_workspace/d9c41ba0845b482cba3db791aff654ed/result.h5",
    "git_ignore_folder/RD-Agent_workspace/bdf83aaec9274db99d8948c862517b1a/result.h5",
    "git_ignore_folder/RD-Agent_workspace/53caa15240204b5c8cfcbc1e129fe77b/result.h5",
    "git_ignore_folder/RD-Agent_workspace/7b90defe90a641dfa964453e3737a8cc/result.h5",
    "git_ignore_folder/RD-Agent_workspace/9d9a76fd399f428cb762680aa88383a9/result.h5",
    "git_ignore_folder/RD-Agent_workspace/ae3530d30d4043ab9707fc2a4e305bd6/result.h5",
    "git_ignore_folder/RD-Agent_workspace/425d7c0433a34655b18e85957f525ff6/result.h5",
    "git_ignore_folder/RD-Agent_workspace/46628d902633464fb8408c68892cb81a/result.h5",
    "git_ignore_folder/RD-Agent_workspace/563ee50916034cda95b6beeb90ef0b4a/result.h5",
    "git_ignore_folder/RD-Agent_workspace/0c3a1839d31c4bec8ee1b45df615b408/result.h5",
    "git_ignore_folder/RD-Agent_workspace/4ced5e16a35f4fe9ab8b41749a91d161/result.h5",
    "git_ignore_folder/RD-Agent_workspace/4c7720d691644c01b4ede9948a2a3700/result.h5",
    "git_ignore_folder/RD-Agent_workspace/fddd8cf67aee4fadacf36efb5524dcb7/result.h5",
    "git_ignore_folder/RD-Agent_workspace/e23d93f1708444ad900972f359e13b85/result.h5",
    "git_ignore_folder/RD-Agent_workspace/b19782da818f4ffc9404c7a5f25e0d47/result.h5",
    "git_ignore_folder/RD-Agent_workspace/b539c7325bce4a46a5ffaafcb0879d81/result.h5",
    "git_ignore_folder/RD-Agent_workspace/cc91d58182ff45419ae330af41183c05/result.h5",
    "git_ignore_folder/RD-Agent_workspace/8d539b7d68a34c90b2f1d8b5daf783f4/result.h5",
    "git_ignore_folder/RD-Agent_workspace/9d846628f9d34fc7bbdfff0a0f9d1e85/result.h5",
    "git_ignore_folder/RD-Agent_workspace/2dd14cf9c124420eace38fd9d6fdca29/result.h5",
    "git_ignore_folder/RD-Agent_workspace/17b83ca9c334476480a0f17433171f82/result.h5",
    "git_ignore_folder/RD-Agent_workspace/5187f367853548c3845a6dc79d17df3e/result.h5",
    "git_ignore_folder/RD-Agent_workspace/2f0fabe9cdf64d2e9c29116e957022ee/result.h5",
    "git_ignore_folder/RD-Agent_workspace/e489b506955942379410db123de74fbf/result.h5",
    "git_ignore_folder/RD-Agent_workspace/0fa748e21d9742ee93c205b46d4fa308/result.h5",
    "git_ignore_folder/RD-Agent_workspace/af541484cd494d2d93e309f1837bddbe/result.h5",
    "git_ignore_folder/RD-Agent_workspace/deae1d21df374081aea5eb8c61921896/result.h5",
    "git_ignore_folder/RD-Agent_workspace/a2221988d2e24c2bb2654468f9579ae1/result.h5",
    "git_ignore_folder/RD-Agent_workspace/eb2c5f8be1ec49a3ba8600b228744ed4/result.h5",
    "git_ignore_folder/RD-Agent_workspace/4d5deb9988b8412bb504f53ae8719951/result.h5",
    "git_ignore_folder/RD-Agent_workspace/58d46eb1227644648fbbc28e935d86c8/result.h5",
    "git_ignore_folder/RD-Agent_workspace/65851d0207a64be193afc900de4c9a20/result.h5",
    "git_ignore_folder/RD-Agent_workspace/36ff3e750dae4f1db9764756b58e3f08/result.h5",
    "git_ignore_folder/RD-Agent_workspace/d41ebcc9e558479289e02f1191c7d804/result.h5",
    "git_ignore_folder/RD-Agent_workspace/b5579d29ae394d9f9798ebafe5f27da5/result.h5",
    "git_ignore_folder/RD-Agent_workspace/c7389713e005416fbacbc7ce2f69d9c2/result.h5",
    "git_ignore_folder/RD-Agent_workspace/23e58f5389ac4a6e879ddbeb2f647021/result.h5",
    "git_ignore_folder/RD-Agent_workspace/b61258c164c941cab4cb83d931a58ca4/result.h5",
    "git_ignore_folder/RD-Agent_workspace/a0835ea266a3419cb2b158a5e14b0f87/result.h5",
    "git_ignore_folder/RD-Agent_workspace/26ecd75f083a4c0e9e28406b50672721/result.h5",
    "git_ignore_folder/RD-Agent_workspace/e5be2dbb2c5c4695a04ba284e2b80340/result.h5",
    "git_ignore_folder/RD-Agent_workspace/53f31d5cf8764bc69fce4ec794a6d961/result.h5",
    "git_ignore_folder/RD-Agent_workspace/ea4d099c09c64dfbb78df15195964b5b/result.h5",
    "git_ignore_folder/RD-Agent_workspace/8379f7edf92d4977b6068454cd5b3315/result.h5",
    "git_ignore_folder/RD-Agent_workspace/caefae9278bc40709bf354310d33ca8a/result.h5",
    "git_ignore_folder/RD-Agent_workspace/57bad9b136d643738865e7956c294a18/result.h5",
    "git_ignore_folder/RD-Agent_workspace/6049317bfa0641ec8b763e010cbe3c04/result.h5",
    "git_ignore_folder/RD-Agent_workspace/7e2b2107d8db4b5ab92e5a56af691450/result.h5",
    "git_ignore_folder/RD-Agent_workspace/d186c1890b69489989fb2d10adc00dd5/result.h5",
    "git_ignore_folder/RD-Agent_workspace/5132ace818914319aa410d9c542aea5d/result.h5",
    "git_ignore_folder/RD-Agent_workspace/0e722659cf2f4a7782a327d6effba63e/result.h5",
    "git_ignore_folder/RD-Agent_workspace/35db9c616c1b4b3aae19211cbadf5569/result.h5",
    "git_ignore_folder/RD-Agent_workspace/84a7c8a288c04935b91f2fe9005fe359/result.h5",
    "git_ignore_folder/RD-Agent_workspace/2fc2109159cf42399086f52866ebe178/result.h5",
    "git_ignore_folder/RD-Agent_workspace/d3ea6f3dfa364d36848f2f8c1681744e/result.h5",
    "git_ignore_folder/RD-Agent_workspace/ef02dd13163745a9952dfb385e7b8272/result.h5",
    "git_ignore_folder/RD-Agent_workspace/c314e50ace5c4e5aab15e0081737e8fb/result.h5",
    "git_ignore_folder/RD-Agent_workspace/852402e46083438cb66d583f591c5332/result.h5",
    "git_ignore_folder/RD-Agent_workspace/f085519de4004a639402f2204084ec69/result.h5",
    "git_ignore_folder/RD-Agent_workspace/9f4869f194344356bc4150a4a2bad3a0/result.h5",
    "git_ignore_folder/RD-Agent_workspace/9d3d08cc087540878d77dee49e7a7aba/result.h5",
    "git_ignore_folder/RD-Agent_workspace/54ffeda710434d67b6608168bd51fb97/result.h5",
    "git_ignore_folder/RD-Agent_workspace/a391db6f6b954d8da96ba513b866c201/result.h5",
    "git_ignore_folder/RD-Agent_workspace/e76c4aa455b5462e9f2d77f6a4d59340/result.h5",
    "git_ignore_folder/RD-Agent_workspace/1e607e3c63304382b24a5d2fdab0c2ad/result.h5",
    "git_ignore_folder/RD-Agent_workspace/e0b072e3d3684e65bf248b686c395626/result.h5",
    "git_ignore_folder/RD-Agent_workspace/5663ce1e33634b639439faeadc234aa8/result.h5",
    "git_ignore_folder/RD-Agent_workspace/480d6077e70345048ebe27b81e316088/result.h5",
    "git_ignore_folder/RD-Agent_workspace/ea714a327ee44cf684c7be3311bff47f/result.h5",
    "git_ignore_folder/RD-Agent_workspace/31dc0405f629461195849303a05bf882/result.h5",
    "git_ignore_folder/RD-Agent_workspace/f9312212fb964b90b81288c4de73cf8e/result.h5",
    "git_ignore_folder/RD-Agent_workspace/002e59fdb57149b7b8ec0dc82d558243/result.h5",
    "git_ignore_folder/RD-Agent_workspace/801577e0a09e4bd78a29e8ece55605c5/result.h5",
    "git_ignore_folder/RD-Agent_workspace/ae6142d2d3aa410e84bf046de590bb8d/result.h5",
    "git_ignore_folder/RD-Agent_workspace/8b5612be297348ccbca1ba0b0b2f0d96/result.h5",
    "git_ignore_folder/RD-Agent_workspace/ae63edaeaac949aea411ae26df0f5221/result.h5",
    "git_ignore_folder/RD-Agent_workspace/bca6b53b0c394f7991890a75291b49f8/result.h5",
    "git_ignore_folder/RD-Agent_workspace/0915a37d229c46a1abbb4cd18bf478f2/result.h5",
    "git_ignore_folder/RD-Agent_workspace/84b631047931438b98c10075947cb221/result.h5",
    "git_ignore_folder/RD-Agent_workspace/4be15a3ebfc4490d9388e62316a874d6/result.h5"
]

print("[*] Starting safe deletion process for corrupted factor files...")

if not FILES_TO_DELETE:
    print("[!] WARNING: The deletion list is empty. No files will be deleted. Exiting.")
    exit()

deleted_count = 0
for file_path in FILES_TO_DELETE:
    print(f"\n--- Processing: {file_path} ---")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"    - [SUCCESS] File has been successfully deleted.")
            deleted_count += 1
        else:
            print(f"    - [INFO] File not found (might have been deleted already). Skipping.")
    except Exception as e:
        print(f"    - [FAILURE] An error occurred while trying to delete the file: {e}")

print(f"\n[*] Deletion process finished. Successfully deleted {deleted_count} file(s).") 