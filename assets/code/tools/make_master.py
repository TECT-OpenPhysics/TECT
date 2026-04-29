import os
import glob

def create_ai_context_file(output_filename="TECT_Merged_Context.txt"):
    # 합칠 파일 확장자 지정 (코드, 텍스트, 로그 등)
    target_extensions = ['*.py', '*.txt', '*.json', '*.md', '*.tex']
    files_to_merge = []
    
    for ext in target_extensions:
        files_to_merge.extend(glob.glob(ext))
        
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        outfile.write("# TECT Research Project - Master Context File\n\n")
        for file_path in files_to_merge:
            # 이 스크립트 자체나 이미 생성된 결과물은 제외
            if file_path == output_filename or file_path == os.path.basename(__file__):
                continue
                
            outfile.write("=" * 60 + "\n")
            outfile.write(f"FILE: {file_path}\n")
            outfile.write("=" * 60 + "\n")
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read() + "\n\n")
            except Exception as e:
                outfile.write(f"[파일 읽기 오류: {e}]\n\n")
                
    print(f"성공: {len(files_to_merge)}개의 파일이 '{output_filename}' 하나로 병합되었습니다. 이 파일만 업로드하십시오.")

if __name__ == "__main__":
    create_ai_context_file()