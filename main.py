from rag_document_viewer import RAG_DV


def main():
    boxes = []
    for i in range(1, 36):
        boxes.append([{
            "page": i,
            "top": 0,
            "left": 0,
            "height": 1,
            "width": 1
        }])
    RAG_DV(file_path="/var/app/test_files/4.pptx", store_path="/var/app/test_files/4_ppt_rag", boxes=boxes)
    
if __name__ == "__main__":
    main()